# model/chat_collection_proto.py # 이후 정비하여 아래로 변경할 것!
# app/services/vector_store_service.py

from app.utils.uuid_utils import new_uuid
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from app.clients.qdrant_client import get_qdrant_client
from llama_index.embeddings.openai import OpenAIEmbedding

embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 캐릭터별 기본 첫 대사 사전 (테스트용)
FIRST_MESSAGES = {
    "0546f43f-9954-4f7c-8ad2-57169efa9c21": "*유진은 제복 소매를 단정히 접으며 당신을 향해 천천히 시선을 든다.*\n무슨 일이오?"
}

# 컬렉션 이름 (하나만 사용)
COLLECTION_NAME = "testChat"

def ensure_collection_exists():
    """testChat 컬렉션이 없으면 생성"""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    names = [c.name for c in collections]

    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        print(f"🟢 Qdrant 컬렉션 생성 완료: {COLLECTION_NAME}")
    else:
        print(f"✅ 이미 존재하는 컬렉션: {COLLECTION_NAME}")


def insert_first_message(perchat_id: str):
    """테스트용 캐릭터 첫 대사를 벡터화 후 testChat 컬렉션에 저장"""
    client = get_qdrant_client()
    ensure_collection_exists()  # perchat_id 인자 제거

    # ① 사전에서 첫 대사 가져오기
    first_message = FIRST_MESSAGES.get(perchat_id)
    if not first_message:
        print(f"❌ FIRST_MESSAGES에 {perchat_id} 항목이 없습니다.")
        return

    # ② 임베딩 생성
    vector = embed_model.get_text_embedding(first_message)

    # ③ Qdrant에 업서트
    point = PointStruct(
        id=str(new_uuid()),
        vector=vector,
        payload={
            "perchat_id": perchat_id,  # 캐릭터 식별용
            "text": first_message,
            "is_first": True
        },
    )

    client.upsert(collection_name=COLLECTION_NAME, points=[point], wait=True)

    print(f"💬 첫 번째 대사 저장 완료 → perchat_id={perchat_id}")
    print(f"등록된 문장: {first_message}")
