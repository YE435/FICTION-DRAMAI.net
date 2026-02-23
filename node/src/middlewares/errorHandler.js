// src/middlewares/errorHandler.js
// 서버 죽지 않고 오류 출력해 주기 위한 기본 뼈대
export const errorHandler = (err, req, res, next) => {
  console.error("[Error]", err.message);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || "Internal Server Error",
  });
};
