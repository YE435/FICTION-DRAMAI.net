# import os
# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
# from llama_index.llms.openai import OpenAI
# from llama_index.embeddings.openai import OpenAIEmbedding
# from llama_index.vector_stores.qdrant import QdrantVectorStore
# from qdrant_client import QdrantClient
# from dotenv import load_dotenv

# # --- 환경변수 로드 ---
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# QDRANT_URL = os.getenv("QDRANT_URL")

# # --- Qdrant 설정 ---
# qdrant_client = QdrantClient(url=QDRANT_URL)
# vector_store = QdrantVectorStore(client=qdrant_client, collection_name="perchat_context")

# # --- 임베딩 & LLM 설정 ---
# embed_model = OpenAIEmbedding(model="text-embedding-3-small")
# llm = OpenAI(model="gpt-4.1-mini", temperature=0.7, max_tokens=800)

# # --- RAG 인덱스 구성 ---
# index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

# def get_model_response(user_message: str, context_docs=None, character_prompt: str = None):
#     """RAG 기반 모델 응답 생성"""
#     query_engine = index.as_query_engine(llm=llm, similarity_top_k=5)
#     context = character_prompt or ""
#     query = f"{context}\n\n사용자: {user_message}\n\n캐릭터로서 답변해 주세요."
#     result = query_engine.query(query)
#     return result.response


# --- 리팩토링 후 버전 (clients 분리) ---
# app/model/perchat_proto.py

from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

# 내부 클라이언트 가져오기
from app.clients.qdrant_client import get_qdrant_client
from app.core.config import settings   # OPENAI_API_KEY 등 환경값 접근

# 컬렉션 첫 대사 저장 로직
from app.model.chat_collection_proto import insert_first_message

# --- Qdrant 설정 ---
qdrant_client = get_qdrant_client()
vector_store = QdrantVectorStore(client=qdrant_client, collection_name="perchat_context")

# --- 임베딩 & LLM 설정 ---
# (API Key는 llama_index 내부에서 openai 패키지가 자동으로 가져가므로 settings에 로드만 되어 있으면 됩니다.)
embed_model = OpenAIEmbedding(model="text-embedding-3-small")
llm = OpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=800)

# --- RAG 인덱스 구성 --- 
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

def get_model_response(user_message: str, perchat_id: str, system_prompt: str = None):
    """RAG 기반 + LLM fallback 응답 생성"""
    insert_first_message(perchat_id)

    # --- 1️⃣ RAG 검색 시도 ---
    retriever = index.as_retriever(similarity_top_k=5)
    retrieved_nodes = retriever.retrieve(user_message)
    has_context = bool(retrieved_nodes)

    # --- 2️⃣ RAG 문맥이 있을 경우 ---
    if has_context:
        chat_engine = index.as_chat_engine(
            chat_mode="context",
            system_prompt=system_prompt,
            llm=llm,
            verbose=True
        )
        result = chat_engine.chat(user_message)
        print("🔍 RAG 기반 응답 생성 완료.")
        return result.response

    # --- 3️⃣ 문맥이 없을 경우 → LLM 단독 응답 ---
    else:
        print("⚠️ 벡터 검색 결과 없음 → LLM 단독 생성으로 전환.")
        prompt = f"{system_prompt.strip() if system_prompt else ''}\n당신은 주로 격식체로 하오체를 사용합니다. 당신의 응답에서 지문은 **사이에, 대사는 따옴표 등의 표시 없이 일반 텍스트로 보내되, 지문과 대사는 줄바꿈으로 표시하십시오.\n\n사용자: {user_message}\n\n캐릭터로서 답변해 주세요."
        result = llm.complete(prompt)
        return result.text
