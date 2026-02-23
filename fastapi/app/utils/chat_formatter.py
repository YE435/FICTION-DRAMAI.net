# utils/chat_formatter.py

def format_chat_history(chats: list[dict]) -> str:
    """
    LLM 입력용 프롬프트 문자열로 변환
    (현재는 텍스트만 포함, 추후 이모티콘/파일 추가 예정)
    """
    formatted = "\n".join(
        [f"{c['chatter']}: {c['chat_content']}" for c in chats if c.get("chat_content")]
    )
    return formatted
