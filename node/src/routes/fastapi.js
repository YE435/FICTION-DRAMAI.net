import { Router } from "express";
import { getHealthFromFastAPI } from "../services/fastapiService.js";

const router = Router();

// FastAPI 연결 테스트용 엔드포인트
router.get("/health", async (_req, res, next) => {
  try {
    const data = await getHealthFromFastAPI();
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
