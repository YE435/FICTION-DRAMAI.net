// react/src/services/signupApi.js
import api from "../lib/api.js";

/**
 * 회원가입
 */
export async function signup({ email, password, nick, contact, role = "user", loginSrc } = {}) {
  if (!email || !password || !nick || !contact) {
    throw new Error("이메일, 비밀번호, 이름, 연락처는 모두 필수입니다.");
  }

  try {
    const res = await api.post("/users/signup", {
      email,
      password,
      nick,
      contact,
      role,
      login_src: loginSrc,
    });
    // 회원가입 후 즉시 발급받은 JWT 토큰 저장
    // FastAPI 응답 구조:
    // { user_uuid, email, nick, access_token, token_type }
    const { email: emailRes, nick: nickRes, access_token } = res.data;
    if (access_token) {
      localStorage.setItem("access_token", access_token);
    }
    if (nick) {
      localStorage.setItem("nick", nickRes);
    }
    if (email) {
      localStorage.setItem("email", emailRes);
    }

    return { ok: true, data: res.data };
  } catch (error) {
    const message = error.response?.data?.message || error.response?.data?.detail || error.message;
    console.error("회원가입 실패:", message);
    return { ok: false, message };
  }
}

/**
 * 사용자 선호 태그 저장 (드라마 + 캐릭터)
 * @param {string} userUuid  회원가입 시 발급된 UUID
 * @param {Array<string>} drama_tags  선택된 드라마 장르들 (["로맨스", "코미디", ...])
 * @param {Array<string>} character_tags  선택된 캐릭터 성향들 (["따스한", "열정적인", ...])
 */
export async function saveUserTags({ drama_tags, character_tags, mode = "signup" }) {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("access_token이 없습니다. 로그인 후 다시 시도해 주세요.");

  if ((!drama_tags || !drama_tags.length) && (!character_tags || !character_tags.length)) {
    throw new Error("저장할 태그가 없습니다.");
  }

  try {
    const method = mode === "edit" ? api.patch : api.post;
    const res = await method(
      "/users/tags",
      { drama_tags, character_tags },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return { ok: true, data: res.data };
  } catch (error) {
    const message =
      error.response?.data?.message || error.response?.data?.detail || error.message;
    console.error("태그 저장 실패:", message);
    return { ok: false, message };
  }
}
