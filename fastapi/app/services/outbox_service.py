# app/services/outbox_service.py
from datetime import datetime, timezone
from app.clients.supabase_client import get_supabase

supabase = get_supabase()

# -----------------------------
# 기본 설정
# -----------------------------
OUTBOX_TABLE = "outbox"

# -----------------------------
# outbox에서 미처리 이벤트 가져오기
# -----------------------------
def fetch_pending_events(task_type: str = "summarize", limit: int = 10):
    """아직 처리되지 않은 outbox 이벤트 목록을 가져온다."""
    res = supabase.table(OUTBOX_TABLE)\
        .select("*")\
        .eq("task_type", task_type)\
        .eq("embed_status", "pending")\
        .lt("retry_count", 3)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    return res.data or []

# -----------------------------
# 처리 성공 시 상태 업데이트
# -----------------------------
def mark_event_done(outbox_idx: int):
    """성공적으로 처리된 이벤트를 완료 상태로 변경"""
    supabase.table(OUTBOX_TABLE).update({
        "embed_status": "done",
        "processed_at": datetime.now(timezone.utc).isoformat()
    }).eq("outbox_idx", outbox_idx).execute()

# -----------------------------
# 처리 실패 시 retry_count 증가
# -----------------------------
def mark_event_failed(outbox_idx: int, max_retry: int = 3):
    """실패 시 재시도 횟수를 증가시키고 상태 유지"""
    data = supabase.table(OUTBOX_TABLE)\
        .select("retry_count")\
        .eq("outbox_idx", outbox_idx)\
        .single()\
        .execute().data
    retry = (data.get("retry_count") or 0) + 1
    status = "failed" if retry >= max_retry else "pending"
    supabase.table(OUTBOX_TABLE).update({
        "retry_count": retry,
        "embed_status": status
    }).eq("outbox_idx", outbox_idx).execute()
