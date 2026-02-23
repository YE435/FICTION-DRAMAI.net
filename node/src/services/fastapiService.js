import axios from "axios";
import { FASTAPI_URL } from "../config/env.js";

// FastAPI와의 통신용 axios 인스턴스 생성
const api = axios.create({
    baseURL: FASTAPI_URL,
    timeout: 10000
});

export const getHealthFromFastAPI = async () => {
  const res = await axios.get(`${FASTAPI_URL}/health`);
  return res.data;
};

export default api;