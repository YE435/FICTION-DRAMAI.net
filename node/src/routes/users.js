import { Router } from "express";
import { signupUser } from "../services/userService.js";
import { verifyJwt } from "../middlewares/authMiddleware.js";
import { saveUserTags } from "../services/userService.js";

const router = Router();

// 회원가입 후 user_uuid, email, nick, access_token 등 반환
router.post("/signup", async (req, res, next) => {
  const { email, password, nick, contact, role = "user", login_src } = req.body;

  if (!email || !password || !nick || !contact) {
    return res.status(400).json({ error: "email, password, nick, contact는 필수입니다." });
  }

  const payload = {
    user_id: email,
    user_pwd: password,
    nick,
    contact,
    role,
    login_src,
  };

  try {
    const user = await signupUser(payload);
    res.status(201).json(user);
  } catch (error) {
    const status = error.response?.status || 500;
    const message = error.response?.data?.detail || error.message;
    error.status = status;
    error.message = message;
    next(error);
  }
});

/**
 * POST /users/tags
 * JWT 검증 후 user_uuid(req.user.sub) 추출 → FastAPI로 전달
 */
router.post("/tags", verifyJwt, async (req, res, next) => {
  const { drama_tags, character_tags } = req.body;
  const userUuid = req.user?.sub;

  if (!userUuid) {
    return res.status(401).json({ error: "Invalid token" });
  }

  if (!Array.isArray(drama_tags) || !Array.isArray(character_tags)) {
    return res.status(400).json({ error: "Invalid tag data format" });
  }

  try {
    const result = await saveUserTags({
      userUuid,
      drama_tags,
      character_tags,
      token: req.token, // (선택 사항) FastAPI 요청 시 헤더 전달용
    });
    res.status(200).json(result);
  } catch (error) {
    next(error);
  }
});


export default router;
