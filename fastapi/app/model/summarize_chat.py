# model/summarize_chat.py
# 과거 대화 20건을 요약하여 벡터 DB에 저장

# DB에서 과거 대화 20건 불러오기 -> services/chatting_service의 list_chat 활용
# 불러온 대화 합치기
# 요약 프롬프트 만들기
# LLM 호출 및 요약 진행
# 벡터 DB 컬렉션 확인 혹은 생성
# 요약본 임베딩
# Points 형식으로 포맷
# 벡터 DB 저장
# 요약한 대화의 meta_data 변경 (summarise:True) - 중복 요약 방지 => db 기능 필요한 이유


# app/model/summarize_chat.py

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# LLM 및 Embedding 모델 전역 초기화
llm = OpenAI(model='gpt-4.1-mini', max_token='512', temperature=0.3)
embedding_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def summarize_recent_chats(chat_texts: list[str]) -> str:
    """최근 대화 20개를 요약문 한 줄로 압축"""
    combined_text = "\n".join(chat_texts)
    prompt = f"""
    다음은 대화 20개의 내용입니다.
    핵심 주제와 공통된 흐름을 한 줄로 요약해줘.

    {combined_text}
    """
    result = llm.complete(prompt)
    return result.text.strip()

def embed_text(text: str) -> list[float]:
    """요약문을 임베딩 벡터로 변환"""
    return embedding_model.get_text_embedding(text)

def get_embedding_dim() -> int:
    """임베딩 차원 수 반환 (Qdrant 컬렉션 생성용)"""
    return embedding_model._model.get_sentence_embedding_dimension()
