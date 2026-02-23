// src/services/roomService.js
import api from "./fastapiService.js";

const authHeaders = (token) =>
  token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};

// 대화방 생성
export async function createRoom({ characId, userUuid, token }) {
  try {
    const payload = {
      charac_id: characId,
      user_uuid: userUuid,
    };

    const res = await api.post("/rooms", payload, {
      headers: authHeaders(token),
    });
    return res.data;
  } catch (err) {
    console.error("❌ FastAPI room 생성 요청 실패:", err.response?.data || err.message);
    throw err;
  }
}

// 대화방 목록 가져오기
export async function getRooms(token, userUuid) {
  try {
    const res = await api.get("/rooms", {
      headers: authHeaders(token),
      params: userUuid ? { user_uuid: userUuid } : undefined,
    });
    return res.data;
  } catch (err) {
    console.error("❌ FastAPI room 요청 실패:", err.response?.data || err.message);
    throw new Error("FastAPI room 요청 실패");
  }
}

// 특정 대화방 정보 조회
export async function getRoom(roomId, token, userUuid) {
  if (!roomId) {
    throw new Error("roomId is required");
  }

  try {
    const res = await api.get(`/rooms/${roomId}`, {
      headers: authHeaders(token),
      params: userUuid ? { user_uuid: userUuid } : undefined,
    });
    return res.data;
  } catch (err) {
    console.error("❌ FastAPI room 상세 요청 실패:", err.response?.data || err.message);
    throw err;
  }
}
