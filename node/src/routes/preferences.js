import { Router } from "express";
import { verifyJwt } from "../middlewares/authMiddleware.js";
import { saveUserTags } from "../services/preferencesService.js";

const router = Router();

router.post("/tags", verifyJwt, async (req, res, next) => {
  const token = req.token;
  try {
    const data = await saveUserTags(req.body, token, "post");
    res.status(201).json(data);
  } catch (error) {
    next(error);
  }
});

router.patch("/tags", verifyJwt, async (req, res, next) => {
  const token = req.token;
  try {
    const data = await saveUserTags(req.body, token, "patch");
    res.json(data);
  } catch (error) {
    next(error);
  }
});

export default router;
