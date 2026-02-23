// services/loginService.js
import api from "./fastapiService.js";

let cachedPublicKey = null;
let cachedAt = 0;
const PUBLIC_KEY_TTL_MS = 60 * 60 * 1000; // 1 hour

// 로그인 → FastAPI에 POST, JWT 반환
export async function loginUser(user_id, user_pwd) {
  try {
    const res = await api.post("/login", { user_id, user_pwd });
    return res.data;
  } catch (error) {
    console.error("Login failed:", error.response?.data || error.message);
    throw error;
  }
}

export async function getPublicKey({ force = false } = {}) {
  const now = Date.now();
  if (!force && cachedPublicKey && now - cachedAt < PUBLIC_KEY_TTL_MS) {
    return cachedPublicKey;
  }

  try {
    const res = await api.get("/auth/public-key", {
      responseType: "text",
    });
    cachedPublicKey = res.data;
    cachedAt = now;
    return cachedPublicKey;
  } catch (error) {
    console.error("Failed to fetch public key:", error.response?.data || error.message);
    throw error;
  }
}

export function clearCachedPublicKey() {
  cachedPublicKey = null;
  cachedAt = 0;
}

