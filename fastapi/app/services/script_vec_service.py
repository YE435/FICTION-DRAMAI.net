# app/services/script_vec_service.py
from __future__ import annotations
from typing import Tuple, Optional, Sequence
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PayloadSchemaType,
    HnswConfigDiff, OptimizersConfigDiff
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext, VectorStoreIndex
from app.clients.qdrant_client import get_qdrant_client
qdrant_client = get_qdrant_client()

COLLECTION_NAME = "script_sum"
VECTOR_NAME = "script_summary"

def ensure_script_sum_index(
    qdrant_client: QdrantClient,
    embedding_model,                       # HuggingFaceEmbedding 등
    payload_indexes: Optional[Sequence[Tuple[str, PayloadSchemaType]]] = None,
):
    """
    - 컬렉션 없으면 생성(네임드 벡터 VECTOR_NAME)
    - payload 인덱스(KEYWORD/INTEGER 등) 멱등 생성
    - QdrantVectorStore + VectorStoreIndex 반환
    """
    # 1) 벡터 차원
    try:
        dim = embedding_model._model.get_sentence_embedding_dimension()
    except Exception:
        # LlamaIndex 임베더 구현체 차이 대응
        dim = getattr(embedding_model, "dimension", None)
        if not dim:
            raise RuntimeError("embedding_model에서 차원을 추출할 수 없습니다.")

    # 2) 컬렉션 존재 여부
    exists = any(c.name == COLLECTION_NAME for c in qdrant_client.get_collections().collections)
    if not exists:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={VECTOR_NAME: VectorParams(size=dim, distance=Distance.COSINE)},
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
            optimizers_config=OptimizersConfigDiff(default_segment_number=2),
        )

    # 3) payload 인덱스(필요 시 추가)
    payload_indexes = payload_indexes or [
        ("drama_id",  PayloadSchemaType.KEYWORD),
        ("episode_no",   PayloadSchemaType.INTEGER),
        ("scene_no",  PayloadSchemaType.INTEGER),
        ("type",      PayloadSchemaType.KEYWORD),   # 'summary' 등
    ]
    for field_name, schema in payload_indexes:
        try:
            qdrant_client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=schema,
            )
        except Exception:
            # 이미 있으면 조용히 스킵
            pass

    # 4) LlamaIndex용 VectorStore/Index 구성
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        vector_name=VECTOR_NAME,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
        embed_model=embedding_model,
    )
    return vector_store, index
