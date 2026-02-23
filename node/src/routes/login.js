// routes/login.js
import { Router } from "express";
import { loginUser, getPublicKey } from "../services/loginService.js";

const router = Router();

router.post("/", async (req, res, next) => {
  const { user_id, user_pwd } = req.body;
  try {
    const data = await loginUser(user_id, user_pwd);
    res.json(data);
  } catch (error) {
    next(error);
  }
});

router.get("/public-key", async (_req, res, next) => {
  try {
    const key = await getPublicKey();
    res.type("text/plain").send(key);
  } catch (error) {
    next(error);
  }
});

export default router;
