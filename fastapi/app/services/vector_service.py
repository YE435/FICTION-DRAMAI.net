# services/vector_service.py
# 벡터 DB (Qdrant) CRUD
from app.clients.qdrant_client import get_qdrant_client
from qdrant_client import models
from qdrant_client.models import VectorParams
client = get_qdrant_client()

# 컬렉션 생성하기
def creat_collection_by_name()

if f"sum_chat_{user_uuid}_and_{charac_name}" not in [c.name for c in qdrant_client.get_collections().collections]:
            dim = embedding_model._model.get_sentence_embedding_dimension()
            qdrant_client.create_collection(
                collection_name=f"sum_chat_{user_uuid}_and_{charac_name}",
                vectors_config={"text_sum" : VectorParams(size=dim, distance="Cosine")},
            )
            
def ensure_collection_exists(collection_name: str, size: int, distance="Cosine"):
    """
    입력한 이름의 컬렉션이 있는지 확인하여 해당 컬렉션의 정보를 반환(CollectionInfo 객체)
    컬렉션이 없을 경우 입력값으로 생성하여 반환
    collection_name : 컬렉션 이름
    size : 컬렉션 내 모든 벡터의 고정된 차원 (임베딩 모델 따라 결정)
    distance : "Cosine" / "Euclid" / "Dot"
    """
    # 존재하는 모든 컬렉션을 가져와 이름만 모은 리스트 만들기
    collections = client.get_collections().collections
    names = [c.name for c in collections]

    # 입력한 이름의 컬렉션이 존재하는지 판단
    if collection_name not in names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=size, distance=distance),
        )
        print("새 컬렉션 생성")
    else:
        print("이미 존재하는 컬렉션")
        
    return client.get_collection(collection_name=collection_name)
# 업서트 하기

# 수정하기

# 검색하기

# 삭제하기