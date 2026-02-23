import { Router } from "express";
import { fetchCharacterById } from "../services/characterService.js";

const router = Router();

router.get("/:characId", async (req, res, next) => {
  const { characId } = req.params;

  try {
    const character = await fetchCharacterById(characId);
    res.json(character);
  } catch (error) {
    next(error);
  }
});

export default router;
