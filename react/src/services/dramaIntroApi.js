// services/dramaIntroApi.js
import api from "../lib/api.js";

export async function fetchCharacterById(id) {
    const res = await api.get(`/characters/${id}`);
    return res.data;
}

// export async function createChatRoom(characId) {
//     if (!characId) {
//         throw new Error("characId가 필요합니다.");
//     }

//     const res = await api.post("/rooms", { charac_id: characId });
//     return res.data;
// }
