import time
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from app.core.config import settings

_qdrant_client = None

def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    print("Qdrant client 초기화 중...")

    for attempt in range(5):
        try:
            client = QdrantClient(
                url=settings.QDRANT_URL
                # api_key=settings.QDRANT_API_KEY # qdrant 배포 후 .env, config.py 등록
            )
            client.get_collections()  # 연결 확인
            print("Qdrant 연결 완료")
            _qdrant_client = client
            return client
        except ResponseHandlingException:
            print(f"Qdrant 아직 준비 중! ({attempt+1}/5)")
            time.sleep(2)

    raise RuntimeError("Qdrant 연결 실패")
