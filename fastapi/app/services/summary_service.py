# app/services/summary_service.py
from qdrant_client.models import VectorParams, Distance
from app.clients.supabase_client import get_supabase
from app.clients.qdrant_client import get_qdrant_client
from app.model.summarize_chat import summarize_recent_chats, embed_text, get_embedding_dim
from app.utils.time_utils import now_utc_iso
from app.utils.uuid_utils import new_uuid

supabase = get_supabase()
qdrant = get_qdrant_client()

TABLE_OUTBOX = "outbox"
TABLE_CHAT = "tb_chatting"

# -------------------------------
# 1️⃣ 쿼리 빌더: outbox 기반
# -------------------------------
def fetch_unsummarized_by_outbox(limit: int = 20):
    """outbox 테이블 기준으로 아직 처리 안 된 chat_id 리스트를 조회"""
    res = supabase.table(TABLE_OUTBOX)\
        .select("chat_id")\
        .eq("task_type", "summarize")\
        .eq("embed_status", "pending")\
        .lt("retry_count", 3)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    chat_ids = [r["chat_id"] for r in res.data]
    if not chat_ids:
        return []
    chats = supabase.table(TABLE_CHAT)\
        .select("*")\
        .in_("chat_id", chat_ids)\
        .order("sent_at", desc=True)\
        .execute()
    return chats.data

# -------------------------------
# 2️⃣ 쿼리 빌더: meta_data 기반
# -------------------------------
def fetch_unsummarized_by_metadata(room_id: str, user_uuid: str, limit: int = 20):
    """meta_data.summarize=false 인 최근 대화만 조회"""
    res = supabase.table(TABLE_CHAT)\
        .select("*")\
        .eq("room_id", room_id)\
        .eq("chatter", user_uuid)\
        .order("sent_at", desc=True)\
        .limit(100)\
        .execute()
    data = [
        d for d in res.data
        if isinstance(d.get("meta_data"), dict)
        and not d["meta_data"].get("summarize", False)
    ]
    return data[:limit]

# -------------------------------
# 3️⃣ 요약 + 저장 로직
# -------------------------------
def summarize_and_store(user_uuid: str, charac_name: str, room_id: str, use_outbox=False):
    """unsummarized 대화만 가져와 요약 후 Qdrant 저장"""
    # 대화 조회
    if use_outbox:
        chats = fetch_unsummarized_by_outbox()
    else:
        chats = fetch_unsummarized_by_metadata(room_id, user_uuid)

    if len(chats) < 20:
        return {"message": "Not enough unsummarized chats."}

    # 대화 내용 추출
    chat_texts = [c["chat_content"] for c in chats if c.get("chat_content")]
    summary_text = summarize_recent_chats(chat_texts)

    # 컬렉션 이름
    collection_name = f"chat_summary_{user_uuid}_{charac_name}"
    existing = [c.name for c in qdrant.get_collections().collections]
    if collection_name not in existing:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config={"text_sum": VectorParams(size=get_embedding_dim(), distance=Distance.COSINE)},
        )

    # 벡터화 및 업로드
    vec = embed_text(summary_text)
    payload = {
        "type": "summary",
        "summary": summary_text,
        "chat_ids": [c["chat_id"] for c in chats],
        "created_at": now_utc_iso()
    }

    qdrant.upsert(
        collection_name=collection_name,
        points=[{
            "id": str(new_uuid()),
            "vector": {"text_sum": vec},
            "payload": payload
        }]
    )

    # meta_data 업데이트
    for c in chats:
        meta = c.get("meta_data", {})
        meta["summarize"] = True
        supabase.table(TABLE_CHAT).update({"meta_data": meta}).eq("chat_id", c["chat_id"]).execute()

    # outbox 상태 업데이트 (선택)
    if use_outbox:
        for c in chats:
            supabase.table(TABLE_OUTBOX)\
                .update({"embed_status": "done", "processed_at": now_utc_iso()})\
                .eq("chat_id", c["chat_id"])\
                .execute()

    return {"summary": summary_text, "status": "success"}
