
#!/usr/bin/env python
# coding: utf-8
from app.clients.openai_client import chat_completion
from app.core.config import settings

# LLM
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

llm = OpenAI(
    model='gpt-4.1-mini',
    max_token='512',
    temperature=0.3,
)
embedding_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# 벡터DB
from app.clients.qdrant_client import get_qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext, VectorStoreIndex

qdrant_client = get_qdrant_client()

from app.clients.supabase_client import get_supabase
from qdrant_client.models import VectorParams, Distance
from qdrant_client.models import Filter, FieldCondition, MatchValue 
from app.services.chatting_service import list_chat

supabase = get_supabase()

 
# =========================================  
# 대화 저장 함수 - save_chat_VecDB
# =========================================  
def save_chat_VecDB(data:dict):
    COLLECTION_NAME = "chat_vectors"    # 단일 컬렉션
    VECTOR_NAME     = "text_dense"      # 네임드 벡터 키
    # 클라이언트 연결
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    memory_index = VectorStoreIndex([], storage_context=storage_context, embed_model=embedding_model)
    # 컬렉션 없을 때 생성하기
    if COLLECTION_NAME not in [c.name for c in qdrant_client.get_collections().collections]:
        dim = embedding_model._model.get_sentence_embedding_dimension()
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={VECTOR_NAME : VectorParams(size=dim, distance=Distance.COSINE)},
        )
    # 데이터 -> 포인트(임베딩된 텍스트 & payload)로 변환
    
    # 텍스트 임베딩
    user_vec = embedding_model.get_text_embedding(f'User: {data["user_text"]}')
    bot_vec = embedding_model.get_text_embedding(f'{data["perchat_name"]}: {data["bot_text"]}')
    
    # payload
    user_payload = {
            "room_id": data["room_id"],
            "chatter": data["user_uuid"],
            "chat_content": data["user_text"],
            "ts": data["ts_user"]
        }
    bot_payload = {
            "room_id": data["room_id"],
            "chatter": data["perchat_id"],
            "chat_content": data["bot_text"],
            "ts": data["ts_bot"]
        }
    # 3) 각각을 개별 PointStruct로 생성
    points = points = [
        {
            "id": data["user_uuid"],
            "vector": {VECTOR_NAME : user_vec},
            "payload": user_payload
        },
        {
            "id": data["perchat_id"],
            "vector": {VECTOR_NAME : bot_vec},
            "payload": bot_payload
        }
    ]
    # 4) Qdrant에 저장
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    # 벡터 DB 삭제 과정 없이
    # # 5) 30개(대화 15턴) 초과시 과거 데이터 삭제
    # # 데이터 불러오기
    # points, _ = qdrant_client.scroll(
    #     collection_name=f"chat_with_{data["perchat_name"]}",
    #     scroll_filter=Filter(
    #         must=[FieldCondition(key="room_id", match=MatchValue(value=room_id))]
    #     ),
    #     with_payload=True,
    #     with_vectors=False,
    #     limit=9999
    # )
    # # 시간순 정렬
    # points_sorted = sorted(points, key=lambda p: p.payload['ts'])
    # # 30개 초과시 이전 대화 삭제
    # if len(points_sorted) > 30 :
    #     to_delete = [p.id for p in points_sorted[:-30]]
    #     qdrant_client.delete(
    #         collection_name=f"chat_with_{data["perchat_name"]}",
    #         points_selector=PointIdsList(points=to_delete)
    #     )

# =========================================  
# 대화 요악본 저장 함수 - sumVecDB
# =========================================  
def save_sum_VecDB(data:dict) :
    # 데이터 sent_at 기준 최신순으로 정렬
    sorted_data = sorted(list_chat(data["room_id"], data["user_uuid"]), key=lambda x: x["sent_at"], reverse=True)
    # 대화의 meta_data의 summarize가 false인 애들만 거르기
    unsum = [
        d for d in sorted_data
        if isinstance(d.get("meta_data"), dict) and d["meta_data"].get("summarize") == False
    ]
    
    if len(unsum) >= 20:
    # chat_content만 추출해서 합치기
        combined_text = "\n".join(
        [d["chat_content"] for d in unsum[:20] if d.get("chat_content")]
        )
        # chat_id만 추출해서 합치기
        combined_meta_data = "\n".join(
            [d["chat_id"] for d in unsum[:20] if d.get("chat_id")]
        )

        # 요약 프롬프트 만들기
        prompt = f"""
        다음은 대화 20개의 내용입니다. 
        지금 현재 상황과 일어나는 사건을 중점으로 요약하세요.
        요약본에는 등장인물과, 장소, 날짜 등이 나와야 합니다.

        {combined_text}
        """

        # LLM 호출
        res = llm.complete(prompt)
        summary = res.text
        # VecDB 연결
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name="sum_chat"
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        memory_index = VectorStoreIndex([], storage_context=storage_context, embed_model=embedding_model)
        
        # 지정 이름의 컬렉션이 없을 경우 생성
        if "sum_chat" not in [c.name for c in qdrant_client.get_collections().collections]:
            dim = embedding_model._model.get_sentence_embedding_dimension()
            qdrant_client.create_collection(
                collection_name="sum_chat",
                vectors_config={"text_sum" : VectorParams(size=dim, distance=Distance.COSINE)},
            )
        # 요약본 임베딩
        sum_vec = embedding_model.get_text_embedding(summary)
        
        # Point 형식으로 포맷
        points = points = [{
            "id" : data["room_id"],
            "vector" : {"text_sum" : sum_vec},
            "payload" : {"chat_id" : combined_meta_data}
        }]
        
        # VecDB 업로드
        qdrant_client.upsert(
            collection_name="sum_chat",
            points=points
        )
        # 요약한 채팅들의 meta_data의 summarize를 True로 전환 (중복 요약 방지)
        for d in unsum[:20]:
            if isinstance(d.get("meta_data"), dict):
                d["meta_data"]["summarize"] = True

            supabase.table("tb_chatting").update({"meta_data" : {"summairze" : True}}).eq("chat_id", d["chat_id"]).execute()