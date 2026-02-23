import express from "express";
import { sendChatMessage, getChatHistory } from "../services/chatService.js";
import { verifyJwt } from "../middlewares/authMiddleware.js";

const router = express.Router();

// 답장 요청
router.post("/", verifyJwt, async (req, res) => {
  const { message, perchat_id: perchatId, room_id: roomId } = req.body;
  const userUuid = req.user?.sub;
  
  console.log("node 요청 접수 완료");
  
  if (!message) {
    return res.status(400).json({ error: "message is required" });
  }
  if (!roomId) {
    return res.status(400).json({ error: "room_id is required" });
  }
  if (!userUuid){
    return res.status(401).json({ error: "Invalid token" });
  }
  console.log("message, roomId, userUuid 확인 완료");
  
  try {
    const response = await sendChatMessage({ message, roomId, perchatId }, req.token);
    console.log("sendChatMessage 실행 완료");
    res.json(response);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// router.get("/", ...) => {
  // const { room_id: roomId } = req.query; // 쿼리 스트링 이용 방식
  // }
// 이전 대화 내역 조회 // GET /chat/{room_id}
router.get("/:room_id", verifyJwt, async (req, res) => {
  const { room_id: roomId } = req.params;
  const userUuid = req.user?.sub;
  const n = req.query.n ? parseInt(req.query.n, 10) : -1; // 최근 n개만 조회한다면 쿼리스트링으로 n값 보내기

  if (!roomId) {
    return res.status(400).json({ error: "room_id is required" });
  }
  if (!userUuid){
    return res.status(401).json({ error: "Invalid token" });
  }
  
  try {
    const history = await getChatHistory(roomId, req.token, userUuid, n);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
