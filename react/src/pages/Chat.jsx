// 25.10.22. 불러오기, 대화 실패 시 모달창 띄우며 사용자 입력 전송 전으로 돌리는 로직 추가
import React, { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import ErrorPopup from "../components/popup/ErrorPopup";

import "../styles/chatLayout.css";                 /* ✅ pages → ../styles */
import "../styles/base.css";

import { MessageCircleQuestion, ChevronLeft, ChevronRight, Search, Bookmark, PlusCircle, Pencil, Type, Moon, Trash2 } from "lucide-react";
import { IoSettingsSharp } from "react-icons/io5"; // 🔄 IoAdd 제거

import MessageList from "../components/chat/MessageList";
import InputBar from "../components/chat/InputBar";
import Sidebar from "../components/chat/Sidebar";
import FindBar from "../components/chat/FindBar";
import TextSizeBar from "../components/chat/TextSizeBar";
import RenameModal from "../components/chat/RenameModal";

import { useAutoResizeTextarea } from "../hooks/useAutoResizeTextarea";
import { useScrollToBottom } from "../hooks/useScrollToBottom";
import * as sidebarFn from "../components/chat/SidebarFunctions";
import * as chatApi from "../services/chatApi";
import { getRoom as getRoomDetail } from "../services/roomApi";

const MAX_TA_HEIGHT = 250;

const normalizeChats = (items, roomTitle) => {
  if (!items) return [];
  const arr = Array.isArray(items) ? items : [items];

  return arr
    .filter(Boolean)
    .map((item) => {
      if (item.from && item.text !== undefined) {
        const isUser = item.from === "me";
        return {
          ...item,
          name: isUser ? item.name || "user" : item.name || roomTitle || "AI",
        };
      }

      const role = (item?.role || "").toLowerCase();
      const isUser = role === "user" || role === "human";
      const text = item?.chat_content ?? item?.text ?? "";
      const id =
        item?.chat_id ||
        `${item?.sent_at || Date.now()}-${item?.turn_id || Math.random()}`;

      return {
        id,
        name: isUser ? "user" : roomTitle || item?.role || "AI",
        from: isUser ? "me" : "you",
        text,
      };
    });
};

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);  // UI용

  // 글씨 크기/다크모드 상태
  const [fontSizeLevel, setFontSizeLevel] = useState(1);   // 1~4 단계
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem("dram_ai_dark");
    return saved ? JSON.parse(saved) : false;
  });

  const [errorMsg, setErrorMsg] = useState(null);
  const [roomInfo, setRoomInfo] = useState(null);
  const [activeRoomId, setActiveRoomId] = useState(null);
  const params = useParams();
  const [searchParams] = useSearchParams();
  const requestedRoomId = params.roomId || searchParams.get("room_id");
  const roomTitle = roomInfo?.room_title || "대화방";
  const navigate = useNavigate(); // url 변경 용도

  useEffect(() => {
    localStorage.setItem("dram_ai_dark", JSON.stringify(isDark)); // 저장
  }, [isDark]);

  // 🔍 채팅 검색 상태
  const [searchQ, setSearchQ] = useState("");      // 검색어
  const [showFind, setShowFind] = useState(false); // 찾기바 표시
  const [matchIdx, setMatchIdx] = useState(-1);    // 활성 매치 인덱스
  const [matchCount, setMatchCount] = useState(0); // 전체 매치 수
  const [showSize, setShowSize] = useState(false);
  const [showRename, setShowRename] = useState(false);     // 모달 표시
  const [roomName, setRoomName] = useState("유진 초이");  // 예시 초기값

  // ref
  const bottomRef = useRef(null);
  const taRef = useRef(null);
  const isRequesting = useRef(false); // useEffect 중복 방지용

  // 훅: 자동 높이 / 맨 아래 스크롤
  useAutoResizeTextarea(taRef, input, MAX_TA_HEIGHT, 36);
  useScrollToBottom(bottomRef, [messages]);

  // 검색어 바뀌면 매치 재계산
  useEffect(() => {
    if (!searchQ) { setMatchCount(0); setMatchIdx(-1); return; }
    const marks = document.querySelectorAll(".hl");
    setMatchCount(marks.length);
    setMatchIdx(marks.length ? 0 : -1);
  }, [searchQ]);

  // 활성 매치 강조 + 스크롤
  useEffect(() => {
    const marks = document.querySelectorAll(".hl");
    marks.forEach(m => m.classList.remove("hl-active"));
    if (matchIdx >= 0 && marks[matchIdx]) {
      const el = marks[matchIdx];
      el.classList.add("hl-active");
      el.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [matchIdx]);
  
    // 최초 1회: 과거 대화 불러오기
  useEffect(() => {
    console.log("🟢 useEffect 실행됨:", requestedRoomId); // useEffect 확인용
    // 요청할 room_id가 없으면 초기화 후 종료
    if (!requestedRoomId) {
      setRoomInfo(null);
      setActiveRoomId(null);
      setMessages([]);
      return;
    }

    // 이미 요청 중이면 아무 것도 하지 않음
    if (isRequesting.current) return;

    let cancelled = false;
    isRequesting.current = true; // 첫 요청만 통과

    const loadRoom = async () => {
      try {
        console.log("⚙️ getRoomDetail 호출:", requestedRoomId);  // /rooms/:roomId 확인용
        const room = await getRoomDetail(requestedRoomId);
        console.log("요청 보냄:", requestedRoomId);
        if (cancelled) return;

        // FastAPI가 새 room_id를 반환했다면 URL 변경
        if (room?.room_id && room.room_id !== requestedRoomId) {
          navigate(`/rooms/${room.room_id}`);
          return;
        }
        
        const effectiveRoomId = room?.room_id;
        let history = [];

        if (effectiveRoomId) {
          history = await chatApi.getHistory(effectiveRoomId);
          if (cancelled) return;
        }

        // 상태 세팅 한 번에
        if (!cancelled) {
          setRoomInfo(room);
          setActiveRoomId(effectiveRoomId || null);
          setMessages(normalizeChats(history, room?.room_title));
          setErrorMsg(null);
        }
      } catch (error) {
        if (!cancelled) {
          console.error("대화방 또는 대화 내역 불러오기 실패:", error);
          setErrorMsg("대화방 정보를 불러오지 못했습니다.");
        }
      } finally{
        setIsLoading(false);
        isRequesting.current = false; // 요청 종료 후 해제
      }
    };

    loadRoom();

    // 실행
    return () => {
      cancelled = true;
    };
  }, [requestedRoomId]);


  // 전송 로직
  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    if (!activeRoomId) {
      setErrorMsg("대화방 정보가 없습니다.");
      return;
    }

    const tempUserId = Date.now();
    const tempTypingId = tempUserId+1;

    // 1) 사용자 메시지 추가
    setMessages(prev => [
      ...prev,
      { id: tempUserId, name: "user", from: "me", text: trimmed }
    ]);      
    setInput("");

    // 2) AI 타이핑
    setMessages(prev => [
      ...prev,
      { id: tempTypingId, name: "유진 초이", from: "you", text: "입력 중..." }
    ]);
    //   { id: tempUserId, name: "user", from: "me", text: trimmed },
    //   { id: tempTypingId, name: roomTitle, from: "you", text: "입력 중..." },
    // ]);

    try {
      setIsLoading(true);

      const aiMessages = await chatApi.getReply(trimmed, { roomId: activeRoomId });
      const normalized = normalizeChats(aiMessages, roomTitle);

      let userRecord = null;
      const botRecords = [];
      normalized.forEach((item) => {
        if (!userRecord && item.from === "me") {
          userRecord = item;
        } else {
          botRecords.push(item);
        }
      });

      const [firstBot, ...restBots] = botRecords;

      setMessages((prev) => {
        const updated = prev.map((m) => {
          if (m.id === tempUserId && userRecord) {
            return { ...userRecord, id: tempUserId };
          }
          if (m.id === tempTypingId && firstBot) {
            return { ...firstBot, id: tempTypingId };
          }
          return m;
        });

        const cleaned = firstBot
          ? updated
          : updated.filter((m) => m.id !== tempTypingId);

        return cleaned.concat(firstBot ? restBots : botRecords);
      });
    } catch (e) {
      console.error("페르챗 응답 실패:", e);
      // 1) 사용자·AI 임시 메시지 제거
      setMessages((prev) =>
        prev.filter((m) => m.id !== tempUserId && m.id !== tempTypingId)
      );

      // 2) 사용자 입력 복원
      setInput(trimmed);

      // 3) 상단 토스트 표시
      setErrorMsg("전송에 실패했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  // Enter 전송, Shift+Enter 줄바꿈
  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 사이드바 핸들러들 (UI는 Chat.jsx, 로직은 sidebarFunctions로 분리)
  const handleOpenCollections = () => { /* TODO: 공감 모아보기 이동 */ };
  const handleNewChat = () => { /* TODO: 새로 대화하기 */ };
  const handleRenameRoom = () => { /* TODO: 대화방 이름 변경 */ };
  const handleFontSizeChange = (e) => setFontSizeLevel(Number(e.target.value));
  const handleToggleDark = (e) => setIsDark(e.target.checked);
  const handleDeleteRoom = () => { /* TODO: 대화방 삭제하기 */ };

  return (

    <div className={`body-wrap chat-scope ${isDark ? "dark" : ""} fs-${fontSizeLevel}`}>
      {/* 에러 메시지 팝업 - 임의 추가*/}
      {errorMsg && (
        <ErrorPopup
          message={errorMsg}
          duration={3500}
          onClose={() => setErrorMsg(null)}
        />
      )}


      {/* 상단 헤더 */}
      <header className="top-header">
        <button
          className="back-btn"
          type="button"                               /* 폼 제출 방지 */
          onClick={() => {
            if (window.history.state?.idx > 0) navigate(-1);  /* 이전 페이지 */
            else navigate("/home");                            /* 첫 진입 보호 */
          }}
        >
          <ChevronLeft className="icon icon-back" />
        </button>

        <div className="peer-info">
          <div className="name">{roomTitle}</div>
        </div>

        <div className="header-actions">
          <button className="icon-btn">
            <MessageCircleQuestion className="icon icon-help" />
          </button>
          <button className="icon-btn" onClick={() => setSidebarOpen(true)}>
            <IoSettingsSharp className="icon icon-gear" />
          </button>
        </div>
      </header>

      <FindBar
        open={showFind}
        keyword={searchQ}
        onChange={setSearchQ}
        onClose={() => { setShowFind(false); setSearchQ(""); }}
        onPrev={() => { if (matchCount) setMatchIdx(p => (p - 1 + matchCount) % matchCount); }}
        onNext={() => { if (matchCount) setMatchIdx(p => (p + 1) % matchCount); }}
        index={matchIdx}
        count={matchCount}
      />

      <TextSizeBar
        open={showSize}
        level={fontSizeLevel}
        onChange={(n) => setFontSizeLevel(n)}
        onClose={() => setShowSize(false)}
      />

      <RenameModal
        open={showRename}                            // 모달 열림 여부
        onClose={() => setShowRename(false)}         // 닫기 함수
        onConfirm={(newName) => console.log("새 이름:", newName)}  // ✅ 반드시 전달!
      />

      {/* 본문 */}
      <main className="home-scroll">
        <div className="chat-body">
          <MessageList
            messages={messages}
            bottomRef={bottomRef}
            isDark={isDark}
            searchQ={searchQ}                 /* 🔍 하이라이트용 검색어 전달 */
          />
        </div>
      </main>

      {/* 입력 바 */}
      <InputBar
        taRef={taRef}
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={isLoading}
        onKeyDown={onKeyDown}
      />

      {/* 사이드바 */}
      <Sidebar open={isSidebarOpen} onClose={() => setSidebarOpen(false)}>
        {/* 메뉴 리스트 (중복 없이 교체) */}
        <nav className="side-list">
          {/* 채팅 검색하기 */}
          <button
            className="side-item"
            onClick={() => {
              setShowFind(true);       // 🔍 찾기바 열기
              setSidebarOpen(false);   // ✅ 사이드바 닫기
            }}
          >
            <Search className="icon" />
            <span>채팅 검색하기</span>
          </button>

          <div className="side-divider"></div>

          {/* 새로 대화하기 */}
          <button className="side-item" onClick={handleNewChat}>
            <PlusCircle className="icon" />
            <span>새로 대화하기</span>
          </button>

          {/* 대화방 이름 변경 */}
          <button className="side-item" onClick={() => { setShowRename(true); setSidebarOpen(false); }}>
            <Pencil className="icon" />
            <span>대화방 이름 변경</span>
          </button>

          <div className="side-divider"></div>

          {/* 글씨 크기 (T 아이콘) */}
          <div className="side-item font-size" style={{ width: "100%" }} onClick={() => {
            setShowSize(true);       // 팝업 열기
            setSidebarOpen(false);   // 사이드바 닫기(원하면 유지)
          }}>
            <Type className="icon" />
            <span>글씨 크기</span>
          </div>

          {/* 바로 아래: 슬라이더 + 눈금 (별도 블록) */}
          <div className="range-wrap">
            <input
              type="range"
              min="1"
              max="4"
              step="1"
              value={fontSizeLevel}
              onChange={(e) => sidebarFn.handleFontSizeChange(e, setFontSizeLevel)}
              autoFocus
            />
            <div className="range-ticks">
              <span>1</span><span>2</span><span>3</span><span>4</span>
            </div>
          </div>

          {/* 다크모드 */}
          <label className="side-item">
            <Moon className="icon" />
            <span>다크모드</span>
            <input
              className="side-switch"
              type="checkbox"
              checked={isDark}
              onChange={handleToggleDark}
            />
          </label>

          <div className="side-divider"></div>

          {/* 대화방 삭제하기 */}
          <button className="side-item chat-exit" onClick={handleDeleteRoom}>
            <Trash2 className="icon" />
            <span>대화방 삭제하기</span>
          </button>
        </nav>
      </Sidebar>
    </div >
  );
}
