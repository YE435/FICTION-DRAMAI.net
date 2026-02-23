import { Router } from "express";
import { verifyJwt } from "../middlewares/authMiddleware.js";
import { createRoom, getRoom, getRooms } from "../services/roomService.js";

const router = Router();

router.get("/", verifyJwt, async (req, res, next) => {
  const userUuid = req.user?.sub;

  if (!userUuid) {
    return res.status(401).json({ error: "Invalid token" });
  }

  try {
    const rooms = await getRooms(req.token, userUuid);
    res.json(rooms);
  } catch (error) {
    next(error);
  }
});

router.post("/", verifyJwt, async (req, res, next) => {
  const { charac_id: characId } = req.body;
  const userUuid = req.user?.sub;

  if (!characId) {
    return res.status(400).json({ error: "charac_id is required" });
  }

  if (!userUuid) {
    return res.status(401).json({ error: "Invalid token" });
  }

  try {
    const room = await createRoom({
      characId,
      userUuid,
      token: req.token,
    });
    res.status(201).json(room);
  } catch (error) {
    next(error);
  }
});

router.get("/:roomId", verifyJwt, async (req, res, next) => {
  const { roomId } = req.params;
  const userUuid = req.user?.sub;

  if (!roomId) {
    return res.status(400).json({ error: "roomId is required" });
  }

  if (!userUuid) {
    return res.status(401).json({ error: "Invalid token" });
  }

  try {
    const room = await getRoom(roomId, req.token, userUuid);
    res.json(room);
  } catch (error) {
    next(error);
  }
});

export default router;
