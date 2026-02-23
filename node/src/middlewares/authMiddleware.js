import jwt from "jsonwebtoken";
import { getPublicKey } from "../services/loginService.js";

export async function verifyJwt(req, res, next) {
  const authHeader = req.headers.authorization || "";
  if (!authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Authorization header missing" });
  }

  const token = authHeader.replace("Bearer", "").trim();
  if (!token) {
    return res.status(401).json({ error: "Token missing" });
  }

  try {
    const publicKey = await getPublicKey();
    const decoded = jwt.verify(token, publicKey, { algorithms: ["RS256"] });
    req.user = decoded;
    req.token = token;
    next();
  } catch (error) {
    console.error("JWT verification failed:", error.message);
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}
