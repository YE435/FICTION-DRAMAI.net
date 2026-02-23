# app/model/perchat_proto_v2.py
# 기존 model_proxy.py와 호환 안 됨.
# 프런트용 응답으로 가공하는 과정을 model_proxy에서 여기로 가져와서 가공된 형식을 보내 줘야 함.
from __future__ import annotations
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.utils.time_utils import now_utc_iso
from app.utils.uuid_utils import new_uuid

# ---- Infra adapters (나중에 infra/로 분리) -------------------------
from app.clients.supabase_client import get_supabase
from app.clients.qdrant_client import get_qdrant_client

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PayloadSchemaType,
    HnswConfigDiff, OptimizersConfigDiff,
    Filter, FieldCondition, MatchValue
)

# 임베딩/LLM (예: HF 임베딩 + LLM 래퍼)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from app.clients.openai_client import chat_completion  # 공용 래퍼(필요 시 교체)

# ---- 상수 ----------------------------------------------------------
COLLECTION_NAME = "chat_vectors"    # 단일 컬렉션
VECTOR_NAME     = "text_dense"      # 네임드 벡터 키

# ---- Qdrant 유틸 ---------------------------------------------------
def ensure_collection_and_indexes(qdrant: QdrantClient, embedding_model) -> None:
    dim = embedding_model._model.get_sentence_embedding_dimension()
    exists = any(c.name == COLLECTION_NAME for c in qdrant.get_collections().collections)
    if not exists:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE)},
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
            optimizers_config=OptimizersConfigDiff(default_segment_number=2),
        )
        logger.info("Qdrant 컬렉션 생성: %s", COLLECTION_NAME)

    # room_id 인덱스(멱등)
    try:
        qdrant.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="room_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        pass  # 이미 있으면 스킵

def qdrant_search(qdrant: QdrantClient, query_vec: List[float], room_id: str, top_k: int = 8) -> List[str]:
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector={VECTOR_NAME: query_vec},
        query_filter=Filter(must=[FieldCondition(key="room_id", match=MatchValue(value=room_id))]),
        limit=top_k,
        with_payload=False,
        with_vectors=False,
    )
    return [str(h.id) for h in hits]

def qdrant_upsert_pair(qdrant: QdrantClient,
                       chat_user_id: str, user_vec: List[float], user_payload: Dict[str, Any],
                       chat_bot_id: str,  bot_vec:  List[float],  bot_payload:  Dict[str, Any]) -> None:
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            {"id": chat_user_id, "vector": {VECTOR_NAME: user_vec}, "payload": user_payload},
            {"id": chat_bot_id,  "vector": {VECTOR_NAME: bot_vec},  "payload": bot_payload},
        ],
    )

# ---- DB 유틸 (Supabase) -------------------------------------------
def insert_chats_bulk(rows: List[Dict[str, Any]]) -> None:
    # 한 요청 = 한 트랜잭션(오토 커밋). 실패 시 예외 처리
    sb = get_supabase()
    res = sb.table("tb_chatting").insert(rows).execute()
    if getattr(res, "error", None):
        raise RuntimeError(res.error)

def load_docs_by_ids(ids: List[str]) -> List[Dict[str, Any]]:
    """RAG용 원문 로딩. 초기엔 단순화: chat_id로 tb_chatting 조회."""
    if not ids:
        return []
    sb = get_supabase()
    res = sb.table("tb_chatting").select("*").in_("chat_id", ids).execute()
    if getattr(res, "error", None):
        logger.warning("DB load_docs_by_ids error: %s", res.error)
        return []
    return res.data or []

# ---- 임베딩/LLM ----------------------------------------------------
EMBED = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def embed_text(text: str) -> List[float]:
    return EMBED.get_text_embedding(text)

def run_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 512) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]
    resp = chat_completion(messages, model="gpt-4.1-mini", temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content

# ---- 컨텍스트 빌드 -------------------------------------------------
def build_rag_context(docs: List[Dict[str, Any]], recent_n: int = 30) -> str:
    if not docs:
        return ""
    # created_at 오름차순 → 최근 N개
    docs_sorted = sorted(docs, key=lambda d: d.get("created_at", ""))
    keep = docs_sorted[-recent_n:]
    lines = [f"{'me' if d.get('role')=='me' else 'you'}: {d.get('chat_content','')}" for d in keep]
    return "최근 대화:\n" + "\n".join(lines)

# ---- 메인 오케스트레이션(한 턴) -----------------------------------
class ChatTurnProcessor:
    """
    입력: data = {
      "room_id", "user_uuid", "perchat_id", "charac_name",
      "turn_id", "user_text", "system_prompt"(옵션)
    }
    출력: {"bot_text", "chat_user_id", "chat_bot_id", "ts_user", "ts_bot"}
    """
    def __init__(self):
        self.qdrant = get_qdrant_client()
        ensure_collection_and_indexes(self.qdrant, EMBED)

    async def process(self, data: Dict[str, Any], top_k: int = 8) -> Dict[str, Any]:
        # 1) 필요 환경 세팅 → __init__에서 수행(컬렉션/인덱스 보장)

        # 2) 사용자 입력 chat_id/ts_user
        chat_user_id = str(new_uuid())
        ts_user = now_utc_iso()

        # 3) 사용자 입력 임베딩
        user_vec = embed_text(f"User: {data['user_text']}")

        # 4) RAG 활용 답변 생성
        # 4-1) Qdrant 검색
        candidate_ids = qdrant_search(self.qdrant, user_vec, room_id=data["room_id"], top_k=top_k)
        # 4-2) 원문 로드 + 프롬프트 조립
        docs = load_docs_by_ids(candidate_ids)
        memory_ctx = build_rag_context(docs, recent_n=30)
        user_prompt = (memory_ctx + "\n\n" if memory_ctx else "") + f"사용자: {data['user_text']}"
        system_prompt = data.get("system_prompt") or f"{data['charac_name']}의 말투와 세계관을 유지하여 답해줘."
        bot_text = run_llm(system_prompt, user_prompt, temperature=0.3, max_tokens=512)

        # 5) 답변 chat_id/ts_bot
        chat_bot_id = str(new_uuid())
        ts_bot = now_utc_iso()

        # 6) 사용자 입력 + AI 답변을 한 번에 DB 저장
        rows = [
            {
                "chat_id": chat_user_id,
                "chatter": data["user_uuid"],
                "role": "me",
                "chat_content": data["user_text"],
                "room_id": data["room_id"],
                "meta_data": {"summarize": False},
                "created_at": ts_user,
            },
            {
                "chat_id": chat_bot_id,
                "chatter": data["perchat_id"],  # 실제 키에 맞게 통일
                "role": "you",
                "chat_content": bot_text,
                "room_id": data["room_id"],
                "meta_data": {"summarize": False},
                "created_at": ts_bot,
            },
        ]
        try:
            insert_chats_bulk(rows)
        except Exception as e:
            logger.error("DB bulk insert 실패: %s", e)
            # 정책: 실패하면 사용자 입력만 반환(봇 응답 미저장)
            return {
                "bot_text": data["user_text"],
                "chat_user_id": chat_user_id, "chat_bot_id": None,
                "ts_user": ts_user, "ts_bot": None,
            }

        # 7) 벡터 DB 저장 (사용자/봇 모두 동일 chat_id로 업서트)
        try:
            bot_vec = embed_text(f"{data['charac_name']}: {bot_text}")
            user_payload = {
                "room_id": data["room_id"], "chatter": data["user_uuid"],
                "chat_content": data["user_text"], "turn_id": data["turn_id"],
                "ts": ts_user, "type": "msg_user",
            }
            bot_payload = {
                "room_id": data["room_id"], "chatter": data["charac_name"],
                "chat_content": bot_text, "turn_id": data["turn_id"],
                "ts": ts_bot, "type": "msg_bot",
            }
            qdrant_upsert_pair(self.qdrant, chat_user_id, user_vec, user_payload,
                               chat_bot_id, bot_vec, bot_payload)
        except Exception as e:
            logger.warning("Qdrant upsert 실패(서비스 지속): %s", e)

        return {
            "bot_text": bot_text,
            "chat_user_id": chat_user_id, "chat_bot_id": chat_bot_id,
            "ts_user": ts_user, "ts_bot": ts_bot,
        }
