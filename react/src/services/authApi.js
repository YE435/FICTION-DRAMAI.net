// react/src/services/authApi.js
import api from "../lib/api.js";

/**
 * 로그인 요청 (Node → FastAPI)
 * @param {Object} param0 email, password
 * @returns access_token 및 상태 메시지
 */
export const authApi = {
  login: async ({ email, password }) => {
    try {
      const res = await api.post("/login", {
        user_id: email,
        user_pwd: password,
      });

      console.log("브라우저에서 로그인을 시도합니다.")
      const { access_token } = res.data;
      console.log("브라우저가 받은 응답을 확인합니다.")
      if (access_token) {
        // 토큰을 localStorage에 저장 (React 클라이언트 인증 유지용)
        localStorage.setItem("access_token", access_token);
        return { ok: true, token: access_token };
      } else {
        return { ok: false, message: "로그인 실패: 토큰이 반환되지 않았습니다." };
      }
    } catch (err) {
      console.error("Login error:", err.response?.data || err.message);
      return {
        ok: false,
        message:
          err.response?.data?.detail || "서버와의 연결 중 문제가 발생했습니다.",
      };
    }
  },

  logout: async () => {
    localStorage.removeItem("access_token");
  },
};

/* 추가: 토큰 관련 함수들 */
export const getToken = () => localStorage.getItem("auth_token");   // 토큰 가져오기
export const removeToken = () => localStorage.removeItem("auth_token"); // 로그아웃용
