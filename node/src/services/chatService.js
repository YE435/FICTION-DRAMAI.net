// src/services/chatService.js
import api from "./fastapiService.js";

const buildHeaders = (token) =>
  token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};

// AI 채팅 요청
export async function sendChatMessage({ message, roomId, perchatId }, token) {
  if (!roomId) {
    throw new Error("roomId is required to send chat message");
  }

  try {
    const payload = {
      message,
      room_id: roomId,
      perchat_id: perchatId || "0546f43f-9954-4f7c-8ad2-57169efa9c21", // 기본 테스트용
    };

    const res = await api.post("/chat", payload, {
      headers: buildHeaders(token),
      params: { room_id: roomId },
    });
    return res.data; // FastAPI는 객체 배열을 반환
  } catch (err) {
    console.error("❌ FastAPI chat 요청 실패:", err.response?.data || err.message);
    throw new Error("FastAPI chat 요청 실패");
  }
}

// 대화 내역 조회
export async function getChatHistory(roomId, token, userUuid, n=-1) {
  if (!roomId) {
    throw new Error("roomId is required to fetch chat history");
  }

  try {
    console.log("➡️ FastAPI로 요청 시도:", `/chat/${roomId}`, n, userUuid);
    // GET /chat/{room_id}
    const res = await api.get(`/chat/${roomId}`, {
      headers: buildHeaders(token),
      params: { 
        node_user_uuid: userUuid,
        n: n,
      },
    });
    
    return res.data;
  } catch (err) {
    console.error("❌ FastAPI chat history 요청 실패:", err.response?.data || err.message);
    throw new Error("FastAPI chat history 요청 실패");
  }
}
