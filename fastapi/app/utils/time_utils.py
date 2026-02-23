# utils/time_utils.py
from datetime import datetime, timezone, timedelta

# 현재 시각을 utc 기준의 iso8601 문자열로 반환
def now_utc_iso():
    return str(datetime.now(timezone.utc))

# utc iso 문자열을 시각을 KST 기준 iso 문자열로 변환
def iso_to_kst(iso_time_str: str) -> str:
    """UTC ISO 문자열을 KST 기준 ISO 문자열로 변환"""
    utc_dt = datetime.fromisoformat(iso_time_str.replace
("Z", "+00:00"))
    kst = timezone(timedelta(hours=9))
    return utc_time.astimezone(kst).isoformat()