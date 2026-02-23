# app/services/chat_vec_service.py
from app.clients.qdrant_client import get_qdrant_client
from qdrant_client import models
from qdrant_client.http import models
from qdrant_client.models import VectorParams
from app.core.logging import logger

qdrant_client = get_qdrant_client()

# 임베딩
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
embedding_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# =========================================  
# 사건 저장 함수 - insert_events_to_vecdb
# ========================================= 
# 원작 사건(캐릭터 입장에서 정리) 벡터 DB에 저장

# ✅ 3️⃣ Qdrant 컬렉션 생성 (처음 1회만)
def create_event_collection(collection_name="yujin_event"):
    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )
    logger.info(f"✅ Created collection: {collection_name}")


# ✅ 4️⃣ 데이터 임베딩 후 VecDB 삽입
def insert_events_to_vecdb(data: dict, collection_name:str="yujin_event"):
    if not data:
        print("⚠️ No event data found.")
        return
    exists = any(c.name == collection_name for c in qdrant_client.get_collections().collections)
    if not exists:
        create_event_collection(collection_name)
        logger.info("Qdrant 컬렉션 생성: %s", collection_name)
    points = []
    for row in data:
        # (1) 텍스트 임베딩
        vec = embedding_model.get_text_embedding(row["details"])

        # (2) Payload 생성
        payload = {
            "event_id": row["event_id"],
            "episode": row["episode"],
            "title": row["title"],
            "location": row["location"],
            "time": row["time"],
            "details": row["details"]
        }

        # (3) Qdrant Point 구성
        point = models.PointStruct(
            id=row["event_id"],  # event_id를 point ID로 사용
            vector=vec,
            payload=payload,
        )
        points.append(point)

    # (4) Qdrant에 업로드
    qdrant_client.upsert(collection_name=collection_name, points=points)
    logger.info(f"✅ {len(points)} events inserted into {collection_name}")
