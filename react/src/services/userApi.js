import { getToken } from "./authApi";  // 기존 authApi에서 토큰 함수 불러오기

// 내 정보 불러오기
export async function fetchMe() {
    const token = getToken();                                              /* 토큰 읽기 */
    const res = await fetch("/api/me", {                                   /* 요청 전송 */
        method: "GET",                                                     /* GET 메서드 */
        headers: {
            "Content-Type": "application/json",                            /* JSON 타입 */
            Authorization: token ? `Bearer ${token}` : "",                 /* 인증 헤더 */
        },
        credentials: "include",                                            /* 쿠키 포함 */
    });

    if (res.status === 401) throw new Error("UNAUTHORIZED");               /* 401 처리 */
    if (!res.ok) throw new Error("FAILED");                                /* 실패 처리 */
    return res.json();                                                     /* JSON 반환 */
}


// src/services/userApi.js
export async function updateMe({ nickname, avatarFile }) {
  // TODO: 백엔드 붙을 때 실제로 구현
  // 예시:
  // const fd = new FormData();
  // fd.append("nickname", nickname);
  // if (avatarFile) fd.append("avatar", avatarFile);
  // const res = await fetch("/api/me", { method: "PUT", body: fd, headers: { Authorization: ... }});
  // if (!res.ok) throw new Error("UPDATE_FAILED");
  // return await res.json();  // { nickname, email, profileUrl }
  throw new Error("BACKEND_NOT_READY");
}