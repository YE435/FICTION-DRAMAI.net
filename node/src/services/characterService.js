import api from "./fastapiService.js";

export async function fetchCharacterById(characId) {
  if (!characId) {
    throw new Error("characId is required");
  }

  const res = await api.get(`/characters/${characId}`);
  return res.data;
}
