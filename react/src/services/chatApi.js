// react/src/services/chatApi.js
import api from "../lib/api.js";

/**
 * 과거 대화 불러오기
 * @param {string} roomId
 * 백엔드가 [{}, {}, ...] 형태의 배열 반환
 */
export async function getHistory(roomId) {
  if (!roomId) {
    console.warn("getHistory 호출에 roomId가 없습니다.");
    return [];
  }
  
  try {
    const res = await api.get(`/chat/${roomId}`); // /chat/{room_id} 요청으로 수정
    // const res = await api.get(`/chat/${roomId}`, { // 쿼리스트링방식 -> 대화 검색에 활용할 것
    //   params: { room_id: roomId },
    // });
    return Array.isArray(res.data) ? res.data : [];
  } catch (e) {
    console.error("대화 내역 불러오기 실패:", e);
    return [];
  }
}

/**
 * AI 답변 요청
 * @param {string} userText
 * @param {{ roomId?: string, perchatId?: string }} options
 * 백엔드가 [{}, {}, ...] 형태의 배열 반환
 */
export async function getReply(userText, { roomId, perchatId } = {}) {
  if (!roomId) {
    throw new Error("getReply 호출에는 roomId가 필요합니다.");
  }

  try {
    const payload = {
      message: userText,
      room_id: roomId,
    };

    if (perchatId) {
      payload.perchat_id = perchatId;
    }

    const res = await api.post("/chat", payload);
    const data = res.data;
    if (Array.isArray(data)) return data;
    return data ? [data] : [];
  } catch (e) {
    console.error("AI 응답 요청 실패:", e);
    throw e;
  }
}
