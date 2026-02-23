# db.py # supabase-py # 10.20. config, client 분리 - 환경 변수 로드 한 번만 진행
# from supabase import create_client, Client
# import os
# from dotenv import load_dotenv

# load_dotenv()
# # 실행 디렉토리나 상위 디렉토리에서 .env 파일 찾음
# # .env 상위 디렉토리인 fastapi/에 있으므로 별도 지정 필요 X

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

"""
기존 코드와의 호환을 유지하면서,
Supabase 클라이언트 초기화는 clients/supabase_client 모듈에 위임.
환경 변수는 core/config.py 에서 관리.
"""

from app.clients.supabase_client import get_supabase

# 기존 코드와 호환성 유지 (기존 import 경로 유지)
supabase = get_supabase()

# 혹시 Depends(get_db) 형태로 주입하는 코드가 있다면 이 함수 유지
def get_db():
    return get_supabase()