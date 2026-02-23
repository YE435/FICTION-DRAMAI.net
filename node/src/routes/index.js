// src/routes/index.js
import { Router } from "express";
import fastapiRoutes from "./fastapi.js";
import loginRoutes from "./login.js";
import roomRoutes from "./room.js";
import userRoutes from "./users.js";
import preferenceRoutes from "./preferences.js";
import characterRoutes from "./characters.js";

const router = Router();

// 헬스체크용 ping 엔드포인트
router.get("/ping", (req, res) => res.send("pong"));

// Node 자체 헬스체크용
router.get("/health", (req, res) => {
  res.status(200).json({ status: "Node API OK" });
});

// FastAPI 관련 라우트
router.use("/fastapi", fastapiRoutes);
router.use("/login", loginRoutes);
router.use("/rooms", roomRoutes);
router.use("/users", userRoutes);
router.use("/users", preferenceRoutes);
router.use("/characters", characterRoutes);

export default router;
