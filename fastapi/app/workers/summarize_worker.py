# app/workers/summarize_worker.py
import time
from datetime import datetime, timezone
from app.services.outbox_service import fetch_pending_events, mark_event_done, mark_event_failed
from app.services.summary_service import summarize_and_store
from app.clients.supabase_client import get_supabase

supabase = get_supabase()

# -----------------------------
# 워커 메인 루프
# -----------------------------
def run_summarize_worker(interval: int = 60):
    """
    요약 임베딩 워커
    - outbox에서 summarize 대기 중인 이벤트를 가져옴
    - 관련 채팅 조회 후 summary_service 호출
    - 처리 결과에 따라 상태 업데이트
    """
    print("🧠 Summarize Worker started.")
    while True:
        try:
            events = fetch_pending_events(task_type="summarize", limit=5)
            if not events:
                time.sleep(interval)
                continue

            for e in events:
                outbox_idx = e["outbox_idx"]
                chat_id = e.get("chat_id")
                target_range = e.get("target_range")
                user_uuid = e.get("user_uuid")
                charac_name = e.get("charac_name")
                room_id = e.get("room_id")

                print(f"🔍 Processing summarize event {outbox_idx} (chat_id={chat_id})")

                try:
                    # summarize_and_store 함수 호출 (outbox 기반)
                    result = summarize_and_store(
                        user_uuid=user_uuid,
                        charac_name=charac_name,
                        room_id=room_id,
                        use_outbox=True
                    )

                    if result.get("status") == "success":
                        print(f"✅ Success: outbox_idx={outbox_idx}")
                        mark_event_done(outbox_idx)
                    else:
                        print(f"⚠️ Skipped: insufficient data (outbox_idx={outbox_idx})")
                        mark_event_done(outbox_idx)

                except Exception as err:
                    print(f"❌ Error processing outbox_idx={outbox_idx}: {err}")
                    mark_event_failed(outbox_idx)

        except Exception as main_err:
            print(f"🚨 Worker loop error: {main_err}")
        finally:
            time.sleep(interval)
