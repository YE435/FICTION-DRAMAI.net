// react/src/services/roomApi.js
import api from "../lib/api.js";
/**
 * 캐릭터 ID를 기반으로 새 대화방 생성
 * @param {string} characId - URL에서 추출된 캐릭터 ID
 */
export async function createRoom(characId) {
  if (!characId) {
    throw new Error("characId가 필요합니다.");
  }
  try {
    const res = await api.post("/rooms", { charac_id: characId });
    return res.data;
  } catch (error) {
    console.error("대화방 생성 실패:", error.response?.data || error.message);
    throw error;
  }
}

/**
 * room_id로 대화방 정보 조회
 * @param {string} roomId
 */
export async function getRoom(roomId) {
  if (!roomId) {
    throw new Error("roomId가 필요합니다.");
  }

  try {
    const res = await api.get(`/rooms/${roomId}`);
    return res.data;
  } catch (error) {
    console.error("대화방 정보 조회 실패:", error.response?.data || error.message);
    throw error;
  }
}

export async function fetchRooms() {
  try {
    const res = await api.get("/rooms");
    return Array.isArray(res.data) ? res.data : [];
  } catch (error) {
    console.error("대화방 목록 조회 실패:", error.response?.data || error.message);
    throw error;
  }
}
