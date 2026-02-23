// src/services/userService.js
import api from "./fastapiService.js";

export async function signupUser(payload) {
  try {
    const res = await api.post("/users/signup", payload);
    return res.data;
  } catch (error) {
    console.error("❌ FastAPI signup 요청 실패:", error.response?.data || error.message);
    throw error;
  }
}

/**
 * FastAPI로 사용자 태그 저장 요청 전달
 * @param {Object} payload - { userUuid, drama_tags, character_tags }
 */
export async function saveUserTags({ userUuid, drama_tags, character_tags, token }) {
  try {
    const res = await api.post(
      "/users/tags",
      {
        user_uuid: userUuid,
        drama_tags,
        character_tags,
      },
      {
        headers: token
          ? { Authorization: `Bearer ${token}` } // ✅ 전달 토큰 (필요 시)
          : undefined,
      }
    );

    return res.data;
  } catch (error) {
    console.error("❌ FastAPI /users/tags 요청 실패:", error.response?.data || error.message);
    throw error;
  }
}