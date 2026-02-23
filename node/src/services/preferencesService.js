import api from "./fastapiService.js";

export async function saveUserTags(payload, token, method = "post") {
  try {
    const config = {
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    };

    const endpoint = "/users/tags";
    const verb = method === "patch" ? api.patch : api.post;
    const res = await verb(endpoint, payload, config);
    return res.data;
  } catch (error) {
    console.error(
      "❌ FastAPI user tags 요청 실패:",
      error.response?.data || error.message
    );
    throw error;
  }
}
