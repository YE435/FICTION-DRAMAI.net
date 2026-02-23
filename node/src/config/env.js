import dotenv from "dotenv";

dotenv.config(); // .env 파일의 변수들을 process.env에 로드

export const PORT = process.env.PORT || 4000;
export const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";
