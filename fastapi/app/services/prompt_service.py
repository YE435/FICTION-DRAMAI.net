# app/services/prompt_service.py
from typing import List, Dict
from app.services.chatting_service import recent_chat_with_names

def build_prompt_from_recent_chats(room_id: str, limit: int = 15) -> str:
    """
    최근 N개의 대화 내역을 불러와 모델 프롬프트 문자열로 변환
    예: "유진 초이: 무슨 일이오.\nuser: 지나다가 들렀습니다."
    """
    # 1) DB에서 최근 대화 불러오기 (이미 시간순으로 정렬된 결과)
    chats: List[Dict] = recent_chat_with_names(room_id, limit)

    # 2) '이름: 내용' 형태로 변환
    lines: List[str] = []
    for chat in chats:
        name = chat.get("name", "Unknown")
        content = chat.get("chat_content", "")
        if not content:
            continue
        lines.append(f"{name}: {content}")

    # 3) 하나의 문자열로 합치기
    prompt = "\n".join(lines)

    return prompt
