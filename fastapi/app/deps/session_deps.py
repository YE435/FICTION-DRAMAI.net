# deps/session_deps.py
# from fastapi import Request, HTTPException

# def get_current_user_uuid(request: Request) -> str:
#     session = request.session
#     user_uuid = session.get("user_uuid")
#     if not user_uuid:
#         raise HTTPException(status_code=401, detail="Not logged in")
#     return user_uuid

# def get_current_room_id(request: Request) -> str:
#     session = request.session
#     room_id = session.get("room_id")
#     if not room_id:
#         raise HTTPException(status_code=400, detail="No active room found in session")
#     return room_id
