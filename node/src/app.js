// src/app.js
import express from "express";
import cors from "cors";
import router from "./routes/index.js";
import chatRouter from "./routes/chat.js";  // 프로토타입v1용 임시 라우트
import { errorHandler } from "./middlewares/errorHandler.js";
// ====== 추가 된 코드 ========
import axios from "axios";
import dotenv from "dotenv";
dotenv.config();


const allowedOrigins = [
  "http://localhost:4000",   // Node 자체 요청 테스트용 
  "http://localhost:3000"   // CRA dev 서버 // Reat dev server 주소
];

// ===== 추가 된 코드 ==================
const app = express();

app.use(cors({
  origin: allowedOrigins, // CRA dev 서버
  credentials: true,  // 세션/쿠키 전달 허용
}));

app.use(express.json());

// 추가
app.use((req, res, next) => {
  console.log(`➡️  ${req.method} ${req.url}`);
  next();
});


app.post("/tts", async (req, res) => {
  try {
    const { text } = req.body;

    const response = await axios.post(
      "https://api.allvoicelab.com/v1/text-to-speech/create",
      {
        text,
        voice_id: "306628930645786629",
        voice_settings: {speed: 1.2}
      },
      {
        headers: {
          "ai-api-key": process.env.ALLVOICE_API_KEY,  // ✅ Authorization 아님
          "Content-Type": "application/json",
        },
        responseType: "arraybuffer"
      }
    );

    res.setHeader("Content-Type", "audio/mpeg");
    res.setHeader("Content-Disposition", "inline; filename=tts.mp3");
    res.send(Buffer.from(response.data)); // ✅ 핵심
  } catch (error) {
    console.error("❌ TTS 요청 실패:", error.response?.data || error.message);
    res.status(500).json({
      error: "TTS 요청 실패",
      message: error.message,
      data: error.response?.data,
    });
  }
});
// ==================================


// 추가
// app.use(cors({
//   origin: function (origin, callback) {
//     const allowedOrigins = [
//       "http://localhost:3000", // React dev
//       "http://localhost:4000", // Node self
//     ];
//     if (!origin || allowedOrigins.includes(origin)) {
//       callback(null, true);
//     } else {
//       callback(new Error("Not allowed by CORS"));
//     }
//   },
//   credentials: true,
// }));



app.use("/api/chat", chatRouter); // 프로토타입v1용 임시 라우트
app.use("/api", router);
app.use(errorHandler);


export default app;
