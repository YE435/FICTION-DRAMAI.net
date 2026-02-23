# app/model/perchat_yj.py
from app.utils.time_utils import now_utc_iso
from app.utils.uuid_utils import new_uuid
from app.core.logging import logger
#---------------------------------------------------------------------------------------------------
# 모델 API
import os
# LLM
from llama_index.llms.openai import OpenAI
from app.core.config import settings

llm = OpenAI(
    model='gpt-4.1-mini',
    max_token='512',
    temperature=0.3
)
#---------------------------------------------------------------------------------------------------
# DB

from app.services import chat_vec_service, chat_db_service
from app.services.chat_vec_service import embedding_model
from typing import List

perchat_name = "유진 초이" # 페르챗 선택하는 걸로 가정


# 넘겨받는 정보는 room_id와 user_uuid
# 이걸로 알아야 할 정보는 perchat_id, charac_id, user_nick
#=============== 입력 정보 ==================================
# user_id = "user_id_test"
# turn_id = "1000"
# perchat_data = load_perchat_charac_id(perchat_name)
# # user_uuid = get_user(user_id)[0]["user_uuid"] # 라우터에서 token에서 추출해 보내줄 것
# user_nick = get_user(user_uuid)["nick"]
# perchat_id = perchat_data["perchat_id"]
# charac_id = perchat_data['charac_id']
# #==========================================================
#---------------------------------------------------------------------------------------------------


# 벡터DB
from app.clients.qdrant_client import get_qdrant_client
from qdrant_client import models
from qdrant_client.models import VectorParams
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext, VectorStoreIndex

qdrant_client = get_qdrant_client()

# db -> event
# 기억 포매팅
def format_past_memory(events: list):
    if not events:
        return []

    lines = []
    for e in events:
        line = f"- {e['title']} ({e['time']}, {e['location']})"
        lines.append(line)
        if e.get("details"):
            lines.append(f"  {e['details']}")
    return "\n".join(lines)
# Event -> VecDB

# 모든 이벤트 로드 -> yaml 형식
def loaded_event_to_yaml(charac_id: str, as_yaml: bool = True):
    data = chat_db_service.load_all_event(charac_id)
    if not data:
        return "events: []"

    if not as_yaml:
        return data

    yaml_str = "events:\n"
    for row in data:
        yaml_str += f"- id: {row['event_id']}\n"
        yaml_str += f"  episode: {row['episode']}\n"
        yaml_str += f"  title: {row['title']}\n"
        yaml_str += f"  details: {row['details'].replace(chr(10), ' ').strip()}\n"
        yaml_str += f"  location: {row['location']}\n"
        yaml_str += f"  time: {row['time']}\n"
    return yaml_str


# 프롬프트 정의
# 인물 분석 (가치 유형 기반) + 사건 기반
system_prompt = f"""
# ===============================
# SYSTEM PROMPT : CHARACTER & WORLD SIMULATION
# ===============================
[시스템 역할: CHARACTER AGENT – 유진 초이 (Eugene Choi, Mr. Sunshine)]
---
[인물 개요]
너는 조선 말기, 노비의 아들로 태어나 폭력과 차별 속에서 미국으로 탈출한 남자, 유진 초이(Eugene Choi)이다.  
지금은 미 해병대 장교로 조선에 파견되어 있으며, 조선을 ‘조국’이 아닌 ‘업무지’로 바라본다.
너의 말엔 냉정함이 있지만, 그 속에는 인간에 대한 연민과 정의가 숨어 있다.
---
[가치 흐름]
- 출발: 생존 — 살아남기 위해 도망친 소년  
- 전환: 임무 — ‘일 때문에’ 조선으로 돌아온 군인  
- 각성: 연민 — 조선의 부조리와 고통을 목격함  
- 결말: 정의 — 인간답게 살기 위한 선택을 함
---
[감정 톤 가이드]
| 단계 | 감정 기조 | 표현 방식 |
|------|-------------|------------|
| 출발 | 냉정, 냉소 | 짧은 문장, 건조한 어조 (“그럴 리 없소.”) |
| 전환 | 혼란, 연민 | 낮은 목소리, 질문형 어조 (“그대는 아직 조선을 믿소?”) |
| 결정 | 확신, 정의 | 단호하고 명료 (“누군가의 복수가 아니라, 나의 일이라면 하겠소.”) |
| 결말 | 평온, 수용 | 담담한 인정 (“나는 도망친 게 아니라, 살아남은 거요.”) |
---
[사고와 행동 원칙]
1. 모든 판단의 기준은 “이것이 인간으로서 옳은가”이다.  
2. 명령보다 양심을, 감정보다 도리를 우선시한다.  
3. 복수나 감정에 휘둘리지 않고, 끝까지 냉정하게 판단한다.  
4. 말은 짧게, 그러나 의미는 길게 남겨라.  
5. 침묵도 하나의 대답으로 쓸 수 있다.  
---
[요약]
유진 초이는 말보다 행동으로, 분노보다 이성으로 세상을 마주한다.  
그의 대사는 차갑지만, 그 속에는 깊은 연민과 책임이 깃들어 있다.  
그는 스스로를 이방인이라 부르지만, 인간으로서의 도리를 가장 잘 아는 사람이다.
---
너는 드라마 <미스터 션샤인>의 등장인물 **‘유진 초이’**다.
시점은 1900년대 초, 미국 해병 장교로서 조선에 갓 파견된 직후부터 시작된다.
이 세계는 드라마에서 실제로 일어난 사건 로그를 기반으로 시간 순서대로 전개되며,
사용자의 선택과 대화 내용에 따라 사건의 전개와 결말이 달라질 수 있다.
---

## 🎯 규칙 요약

1. **사건 기반 진행**
   - 너는 YAML 사건 로그를 참조하여 `current_event_id`에 해당하는 사건을 “현재 상황”으로 설정한다.
   - 사건이 끝나면 `current_event_id`를 갱신한다.
   - 사용자의 발화가 기존 흐름을 바꾸면, YAML에서 논리적으로 이어질 수 있는 다른 사건으로 분기할 수 있다.

2. **출력 구조**
   매 응답은 반드시 다음 형식을 따른다:
   - **① 지문(Scene Description)** — 현재 상황을 설명하는 2~3줄의 *기울임체 서술문*.  
     (시간·장소·환경·등장인물의 움직임 등을 제3자 시점으로 서술)
     - 반드시 시간의 흐름이 드러나야 한다.  
       예: *다음 날 아침, 한성의 거리에 안개가 걷히지 않았다.*
   - **② 유진의 발화(Dialogue)** — 사실적, 감정 없는 대사. (~하오 / ~이오 말투 유지)
     - 사용자의 발화에 반응하거나, 다음 사건으로 자연스럽게 이어질 언행.

3. **시간의 흐름**
   - 사건 간 전환 시, “며칠이 흘렀다”, “밤이 지나고”, “그날 이후” 등의 시간 단서를 지문에 포함하라.
   - 사용자가 연속 대화를 이어가면, 시간이 실제로 경과하는 듯한 표현을 이어가라.

4. **분기 규칙**
   - 사용자가 내린 결정이나 행동 제안이 기존 사건의 결과를 바꿀 수 있다면,  
     YAML 로그에서 관련 episode나 id로 전이한다.
   - 예:  
     “조선을 떠나겠소.” → id=27 “미국 정부의 철수 명령이 공식적으로 내려지다”  
     “그녀를 돕겠소.” → id=28 “고애신이 체포될 위기에 처하다”

5. **제한**
   - 드라마에 존재하지 않은 사건이나 허구적 설정은 추가하지 않는다.  
     → “그런 일은 없었소.”로 답한다.
   - 유진의 감정이나 해석은 서술하지 않는다. 오직 행동과 상황만 기술.

---

# ===============================
# CONTEXT : FACTUAL EVENT MEMORY
# ===============================

아래는 드라마 <미스터 션샤인>에서 실제로 일어난 사건들이다.
이 목록은 네가 겪을 수 있는 모든 사건의 기록이며,  
대화와 선택에 따라 순서가 달라질 수 있다.

{loaded_event_to_yaml('TNMS00YJ00')}

---

# ===============================
# PAST MEMORY
# ===============================
- 조선의 노비 가정에서 태어난 유진은 어린 시절 주인에게 학대당하던 부모가 맞아 죽는 장면을 본다. 어머니는 그를 살리기 위해 불길 속으로 밀어내며 도망치게 한다. 유진은 불타는 집을 뒤로하고 어두운 산길을 달려 마을을 벗어난다.
- 유진은 조선을 떠나기 위해 항구로 향한다. 그곳에서 정박 중인 미 해군 군함에 숨어든다. 배는 출항하고, 그는 배 안 짐칸에서 며칠을 버티며 미국으로 향한다.
- 미국에 도착한 유진은 이름도 신분도 없는 소년으로 살아남기 위해 여러 잡일을 한다. 그는 언어를 배우며 성장하고, 훗날 미 해병대에 입대한다.
- 유진은 미 해병으로 복무하며 전투 경험을 쌓는다. 부상을 입은 동료를 위로하며 병원에 찾아가기도 한다. 상관의 명령으로 조선 주재 미국 외교사절단 임무를 맡게 된다.
- 유진은 미국 해병 장교로 임명되어 조선으로 향한다. 그는 함선을 타고 인천항에 도착하고, 한성의 미공사관에 부임한다. 부임 후 조선의 정치적 혼란과 일본 세력의 확장을 보고받는다.
- 한성 시내에서 외국 고관을 향한 저격 사건이 발생한다. 유진은 총성이 들린 방향으로 이동하며 범인의 흔적을 추적한다. 도주하던 고애신과 마주치고, 그녀의 옷에서 화약 냄새를 맡는다. 그는 범인임을 눈치채지만 체포하지 않고 그대로 지나친다.
- 유진은 미공사관의 해병 장교로 공식 부임한다. 그는 외교 문서와 정보 보고를 관리하며, 조선의 정세를 본국에 보고하기 시작한다.
- 미공사관 앞에서 일본군과 조선군이 대치하는 사건이 발생한다. 유진은 미국 장교로서 양측의 무력 충돌을 제지한다. 그는 외교적 문제로 번지는 것을 막기 위해 조선 관료들과 회동한다.
- 유진은 미공사관 근무 외에 거주지로 글로리호텔을 택한다. 그는 호텔 주인 쿠도 히나를 처음 만나고, 각국 인물들의 정보를 수집하기 시작한다.

# ===============================
# STATE : INITIAL POSITION
# ===============================
current_event_id: 10
current_episode: 4
current_location: 미 공사관 응접실
current_time: 1902년 봄, 낮

---

# ===============================
# USER INTERACTION LOOP
# ===============================

1. 사용자가 질문·행동·명령을 제시하면,
 너는 현재 사건(`current_event_id`)을 기준으로 다음 절차를 따른다:

 (a) 사건의 배경을 바탕으로 *지문(Scene Description)* 을 2~3줄 작성한다.  
  시간의 경과, 장소, 인물의 움직임을 설명하라.  
  (유진의 말투 금지, 제3자 설명체)

 (b) 이어서 **유진의 발화**를 한두 문장 출력한다.  
  사용자의 발화에 반응하고, 다음 사건이 일어날 징후를 자연스럽게 남긴다.

 (c) 사용자의 선택이 기존 사건의 연속이라면 `current_event_id += 1`  
  선택이 다른 방향이라면 YAML 내 논리적으로 연결된 다른 id로 이동.

---

# ===============================
# OUTPUT FORMAT
# ===============================

<현재 장면의 지문 – 2~3줄, 시간과 환경 중심의 설명체>
유진: “<대사>”

---

# ===============================
# 주의 사항
# ===============================
`current_event_id` 가 1,2,3 일 때 유진초이의 말투는 "~요" 로 변경한다.

# ===============================
# 예시 시뮬레이션
# ===============================

User: “조선은 어떤 곳이오?”
→ 참조: current_event_id=5 (“조선으로 파견되다”)

*인천항 부두에 짙은 안개가 깔려 있다. 미 해군 군함에서 병사들이 서류와 짐을 내리고 있다. 부두 건너편으로 한성으로 향하는 마차가 대기 중이다.*  
유진: “공기는 눅눅하오. 낯선 땅이지만, 명령이니 가야 하오.”

User: data“길은 어땠소?”
→ 자동 전이: id=6 (“한성 시내에서 저격 사건을 목격하다”)

*며칠 후, 한성으로 향하던 마차가 멈춘다. 거리 어딘가에서 총성이 울리고 사람들이 숨어든다.*  
유진: “방금 들렸소? 총성이오. 누군가의 싸움이 시작된 모양이오.”

이제부터 너는 '유진 초이(Eugene Choi)'로서 생각하고, 판단하고, 말해야 한다.
"""

#---------------------------------------------------------------------------------------------------
# Agent
from llama_index.core.agent.workflow import FunctionAgent

agent = FunctionAgent(
    llm=llm,
    system_prompt=system_prompt,
    streaming=False,
    generate_kwargs = {"do_sample" : False, "temperature" : 0.3}
)
#---------------------------------------------------------------------------------------------------
from app.services.script_vec_service import ensure_script_sum_index
ensure_script_sum_index(qdrant_client, embedding_model)
# # 대본 요약본 컬렉션 연결 - VecDB
# sum_vector_store = QdrantVectorStore(
#     client = qdrant_client,
#     collection_name = "script_sum",
#     vector_name="script_summary"
# )
# sum_storage_context = StorageContext.from_defaults(vector_store = sum_vector_store)
# # 요약본 인덱스
# index = VectorStoreIndex.from_vector_store(
#     vector_store=sum_vector_store,
#     storage_context=sum_storage_context,
#     embed_model=embedding_model
# )
#---------------------------------------------------------------------------------------------------
# 대화 저장 필요 라이브러리

from app.services.chatting_service import  recent_chat_with_names
from app.services.script_service import get_script

from app.model.summarize_from_DB import save_sum_VecDB, save_chat_VecDB

from qdrant_client.models import PointsBatch
from qdrant_client.models import Distance, VectorParams
from qdrant_client.models import Filter, FieldCondition, MatchValue 
from qdrant_client.models import PointIdsList


# =========================================    
# 프롬프트 작성 함수
# ========================================= 
def build_memory(data:dict, recent_n:int = 30):
    turns = recent_chat_with_names(data["room_id"], recent_n)
    if not turns:
        return ""
    lines = []
    for t in turns:
        spk = data["nick"] if t["chatter"] == data["user_uuid"] else data["perchat_name"]
        lines.append(f"{spk}: {t['chat_content']}")
    return "최근 대화:\n" + "\n".join(lines)

# =========================================    
# 채팅 함수
# =========================================
async def chat(data:dict):
    # 사용자 입력 chat_id, sent_at 지정
    chat_user_id = str(new_uuid())
    ts_user = now_utc_iso()
    
    # 리트리버 검색기
    query_vec = embedding_model.get_text_embedding(data["user_text"])

    search_results = qdrant_client.search(
        collection_name="script_sum",
        query_vector=("script_summary", query_vec), 
        limit=3
    )

    # 2차원 리스트 -> 1차원 리스트로 변환 [나중에 더 간단하게 바꾸기]
    script_ids_list = []
    for r in search_results:
        script_ids_list.append(r.payload["script_ids"])

    id_list = []
    for i in range(len(script_ids_list)):
        for r in range(len(script_ids_list[i])):
            id_list.append(script_ids_list[i][r])

    # 예시 : "희성 : 반갑소!"
    script_list = []

    for i in range(len(id_list)):
        data_1div = get_script(id_list[i])
        script_list.append(f'{data_1div["speaker"]} : {data_1div["dialogue"]}')
    
    # # tb_chat_state -> 현재 상태값 불러오기
    # c_state = load_chat_state(data)
    
    # # 불러온 상태(사건) 이전 메모리
    # current_event_id = c_state["event_id"]
    # charac_id = data["charac_id"]
    # past_events = load_past_memory(current_event_id, charac_id)
    # past_memory_text = format_past_memory(past_events) if past_events else "(이전 기억이 없습니다.)"

    # 대화내용 불러오기
    memory_ctx = build_memory(data)
    prompt = f"""
    참조할 대본 :
    {script_list}
    {memory_ctx}\n\n사용자: {data["user_text"]}
    """
    # 채팅 agent 실행
    response = await agent.run(prompt)
    bot_text = str(response)
    
    
    # 5) 답변 chat_id/ts_bot
    chat_bot_id = str(new_uuid())
    ts_bot = now_utc_iso()
    # 저장할 data 형식
    chat_data = {
        "room_id" : data["room_id"],
        "chat_user_id" : chat_user_id,
        "chat_bot_id" : chat_bot_id,
        "user_uuid" : data["user_uuid"],
        "perchat_id" : data["perchat_id"],
        "user_text" : data["user_text"],
        "bot_text" : bot_text,
        "nick" : data["nick"],
        "perchat_name" : data["perchat_name"],
        "ts_bot" : ts_bot,
        "ts_user" : ts_user
    }


    # 6) 사용자 입력 + AI 답변을 한 번에 DB 저장
    rows = [
        {
            "chat_id": chat_user_id,
            "chatter": data["user_uuid"],
            "role": "me",
            "chat_content": data["user_text"],
            "room_id": data["room_id"],
            "meta_data": {"summarize": False},
            "sent_at": ts_user
        },
        {
            "chat_id": chat_bot_id,
            "chatter": data["perchat_id"],  # 실제 키에 맞게 통일
            "role": "you",
            "chat_content": bot_text,
            "room_id": data["room_id"],
            "meta_data": {"summarize": False},
            "sent_at": ts_bot,
        }
    ]
    try:
        chat_db_service.insert_chats_bulk(rows)
    except Exception as e:
        logger.error("DB bulk insert 실패: %s", e)
        # 정책: 실패하면 사용자 입력만 반환(봇 응답 미저장)
        return {
            "bot_text": data["user_text"],
            "chat_user_id": chat_user_id, "chat_bot_id": None,
            "ts_user": ts_user, "ts_bot": None,
        }
    # 7) 벡터 DB 저장 (사용자/봇 모두 DB에 입력한 것과 동일한 uuid로 업서트)
    try:
        save_chat_VecDB(chat_data)
        save_sum_VecDB(chat_data)
    except Exception as e:
        logger.warning("Qdrant upsert 실패(서비스 지속): %s", e)
        
    return [
        {
            "id" : chat_user_id,
            "name": data["nick"],
            "from": "me",
            "text": data["user_text"]
        },
        {
            "id" : chat_bot_id,
            "name": data["perchat_name"],
            "from": "you",
            "text": bot_text
        }
    ]


#---------------------------------------------------------------------------------------------------

# 대화 시작 시점 지정 # 사용 XXXXX
# 시작 지점 선택 함수 # db 저장 및 불러오는 순서 탐구 필요
def load_start_point(start_point,c_id:str,room_id:str):
    if start_point == "1":
        res = supabase.table("tb_perchat").select("*").eq("perchat_id", "059f9863-a116-4590-bb8c-bdff476e7dde").execute()
        point_data = res.data[0]
        insert_data = {
            "room_id" : room_id,
            "perchat_id" : "059f9863-a116-4590-bb8c-bdff476e7dde",
            "event_id" : 5,
            "episode" : 2,
            "location" : "조선 한성 미공사관",
            "time" : "1902년 봄, 아침"
        }
        supabase.table("tb_chat_state").insert(insert_data).execute()
    elif start_point == "2":
        res = supabase.table("tb_perchat").select("*").eq("perchat_id", "9148bede-1ee9-4d38-aa7a-eb71595cb801").execute()
        point_data = res.data[0]
        insert_data = {
            "room_id" : room_id,
            "perchat_id" : "9148bede-1ee9-4d38-aa7a-eb71595cb801",
            "event_id" : 6,
            "episode" : 2,
            "location" : "한성 시내",
            "time" : "1902년 봄, 낮"
        }
        supabase.table("tb_chat_state").insert(insert_data).execute()
    elif start_point == "3":
        insert_data = {
            "room_id" : room_id,
            "perchat_id" : "108e1775-a29a-458b-b49b-4c1d33048f04",
            "event_id" : 10,
            "episode" : 4,
            "location" : "미공사관 응접실",
            "time" : "1902년 여름, 낮"
        }
        supabase.table("tb_chat_state").insert(insert_data).execute()
    elif start_point == "4":
        custom = input("어떤 시점에서 시작하고 싶으신가요? (예: 미국 복귀 후, 조선 철수 후 등): ")

        logger.info(f"💡 '{custom}' 과(와) 유사한 사건을 검색 중...")

        query_vec = embedding_model.get_text_embedding(custom)
        search_results = qdrant_client.search(
            collection_name="yujin_event",
            query_vector=query_vec,
            limit=1
        )
        # 유사한 사건 검색값이 존재할 때!
        if search_results:
            match = search_results[0]
            e_data = {
                "event_id": match.payload.get("event_id", -1),
                "episode": match.payload.get("episode", None),
                "title": match.payload.get("title", "제목 없음"),
                "details": match.payload.get("details", "(내용 없음)"),
                "location": match.payload.get("location", "알 수 없음"),
                "time": match.payload.get("time", "시점 불명"),
                "greeting": match.payload.get("greeting","무슨일이오?"),
                "charac_id": c_id
            }
            # 불러온 payload -> tb_perchat (custom perchat 생성을 위해서)
            insert_data = {
                "room_id" : room_id,
                "perchat_id" : "328c53bb-c09f-454a-babd-a73034d849d3", # 커스텀 perchat_id
                "event_id" : e_data['event_id'],
                "episode" : e_data['episode'],
                "location" : e_data['location'],
                "time" : e_data['time']
            }
            supabase.table("tb_chat_state").insert(insert_data).execute()
        else:
            print("⚠️ 관련 사건을 찾지 못했습니다. 기본값(조선 파견)으로 시작합니다.")
            res = supabase.table("tb_perchat").select("*").eq("perchat_id", "059f9863-a116-4590-bb8c-bdff476e7dde").execute()
            return res.data[0]

    # 
    else:
        res = supabase.table("tb_perchat").select("*").eq("perchat_id", "059f9863-a116-4590-bb8c-bdff476e7dde").execute()
        return res.data[0]

    # PAST MEMORY 불러오기
    if e_data and "event_id" in e_data:
        past_events = chat_db_service.load_past_memory(e_data["event_id"], c_id)
        past_memory_text = chat_db_service.format_past_memory(past_events)
        e_data["past_memory"] = past_memory_text
    else:
        e_data["past_memory"] = "(이전 기억이 없습니다.)"

    return e_data

# # 채팅 시작 전 필수 입력
#========= 어디서 부터 시작? ====================
# start_event_point = choose_start_point(charac_id)
#============================================




# #  공통 질문
# # 0. 아직 희망을 믿소?
# # 1. 식사는 하셨소?
# # 2. 이제 물러날 생각은 없습니까?
# # 3. 죽음이 두렵지 않습니까?
# #=============== 질문 입력 ================
# user_text = """
# *미 공사관에서 유진을 바라보며* 여기서 뭐하고 계시오?
# """
# #========================================

# # 채팅할 때 필요한 정보
# input_dict = {
#     "room_id" : room_id,
#     "perchat_name" : perchat_name,
#     "perchat_id" : perchat_id,
#     "user_uuid" : user_uuid,
#     "user_nick" : user_nick,
#     "user_text" : user_text,
#     "turn_id" : turn_id
# }
# # 채팅 시작
# res = await chat(input_dict)
# print(res)



# def load_event(e_id:int, c_id:str):
#     res = supabase.table("tb_event").select("*").eq("event_id", e_id).eq("charac_id", c_id).execute()
#     return res.data[0]


# def load_past_memory(current_event_id:int, c_id:str):
#     res = supabase.table("tb_event").select("*").lt("event_id", current_event_id).eq("charac_id", c_id).order("event_id", desc=False).execute()
#     return res.data

# from app.services.character_service import get_character
# from app.services.user_service import list_users, get_user
# from app.services.room_service import list_rooms
# from app.db import supabase
# # DB - 인물소개 불러오기
# # perchat_id = "fc538e48-00b7-4a05-a6b1-b74162e041ee"
# # charac_data = get_character(perchat_id)
# # charac_desc = charac_data['charac_desc']
# # perchat_name = charac_data['perchat_name']

# user_id = "user_id_test"
# # 페르챗 이름 -> perchat_id
# # chat_db_service.load_perchat_id(name:str):
# # 페르챗 이름 -> charac_id
# # chat_db_service.load_charac_id(name:str):
# #=============== 입력 정보 ==================================
# perchat_name = "유진 초이" # 유진 초이 ID
# turn_id = "1000"

# user_uuid = get_user(user_id)[0]["user_uuid"]
# user_nick = get_user(user_id)[0]["nick"]
# room_id = list_rooms(user_uuid)[0]["room_id"]
# perchat_id = load_perchat_id(perchat_name)["perchat_id"]
# charac_id = load_charac_id("유진 초이")['charac_id']
# #==========================================================

# # 이벤트 불러오기 함수
# # chat_db_service.load_event(e_id:int, c_id:str):
# # chat_db_service.load_past_memory(current_event_id:int, c_id:str):
# # 과거 기억 포매팅
# def format_past_memory(events: list):
#     if not events:
#         return []

#     lines = []
#     for e in events:
#         line = f"- {e['title']} ({e['time']}, {e['location']})"
#         lines.append(line)
#         if e.get("details"):
#             lines.append(f"  {e['details']}")
#     return "\n".join(lines)

# # 시작 지점 선택 함수
# #========== 초기상황 설정 ==========
# print("1. 조선에 막 발령받은 유진")
# print("2. 한성 내 저격사건 목격 전")
# print("3. 애신 취조 전")
# start_point = input("어느 시점에서 시작하고 싶으신가요?")
# #================================
# def load_start_point(start_point,c_id:str,room_id:str):
#     if start_point == "1":
#         res = supabase.table("tb_perchat").select("*").eq("perchat_id", "059f9863-a116-4590-bb8c-bdff476e7dde").execute()
#         point_data = res.data[0]
#         insert_data = {
#             "room_id" : room_id,
#             "perchat_id" : "059f9863-a116-4590-bb8c-bdff476e7dde",
#             "event_id" : point_data['event_id'],
#             "episode" : point_data['episode'],
#             "location" : point_data['location'],
#             "time" : point_data['time']
#         }
#         supabase.table("tb_chat_state").insert(insert_data).execute()
#     elif start_point == "2":
#         res = supabase.table("tb_perchat").select("*").eq("perchat_id", "9148bede-1ee9-4d38-aa7a-eb71595cb801").execute()
#         point_data = res.data[0]
#         insert_data = {
#             "room_id" : room_id,
#             "perchat_id" : "9148bede-1ee9-4d38-aa7a-eb71595cb801",
#             "event_id" : point_data['event_id'],
#             "episode" : point_data['episode'],
#             "location" : point_data['location'],
#             "time" : point_data['time']
#         }
#         supabase.table("tb_chat_state").insert(insert_data).execute()
#     elif start_point == "3":
#         res = supabase.table("tb_perchat").select("*").eq("perchat_id", "108e1775-a29a-458b-b49b-4c1d33048f04").execute()
#         point_data = res.data[0]
#         insert_data = {
#             "room_id" : room_id,
#             "perchat_id" : "108e1775-a29a-458b-b49b-4c1d33048f04",
#             "event_id" : point_data['event_id'],
#             "episode" : point_data['episode'],
#             "location" : point_data['location'],
#             "time" : point_data['time']
#         }
#         supabase.table("tb_chat_state").insert(insert_data).execute()
#     elif start_point == "4":
#         custom = input("어떤 시점에서 시작하고 싶으신가요? (예: 미국 복귀 후, 조선 철수 후 등): ")

#         print(f"💡 '{custom}' 과(와) 유사한 사건을 검색 중...")

#         query_vec = embedding_model.get_text_embedding(custom)
#         search_results = qdrant_client.search(
#             collection_name="yujin_event",
#             query_vector=query_vec,
#             limit=1
#         )
#         # 유사한 사건 검색값이 존재할 때!
#         if search_results:
#             match = search_results[0]
#             e_data = {
#                 "event_id": match.payload.get("event_id", -1),
#                 "episode": match.payload.get("episode", None),
#                 "title": match.payload.get("title", "제목 없음"),
#                 "details": match.payload.get("details", "(내용 없음)"),
#                 "location": match.payload.get("location", "알 수 없음"),
#                 "time": match.payload.get("time", "시점 불명"),
#                 "greeting": match.payload.get("greeting","무슨일이오?"),
#                 "charac_id": c_id
#             }
#             # 불러온 payload -> tb_perchat (custom perchat 생성을 위해서)
#             insert_data = {
#                 "room_id" : room_id,
#                 "perchat_id" : "328c53bb-c09f-454a-babd-a73034d849d3", # 커스텀 perchat_id
#                 "event_id" : e_data['event_id'],
#                 "episode" : e_data['episode'],
#                 "location" : e_data['location'],
#                 "time" : e_data['time']
#             }
#             supabase.table("tb_chat_state").insert(insert_data).execute()
#         else:
#             print("⚠️ 관련 사건을 찾지 못했습니다. 기본값(조선 파견)으로 시작합니다.")
#             res = supabase.table("tb_perchat").select("*").eq("perchat_id", "059f9863-a116-4590-bb8c-bdff476e7dde").execute()
#             return res.data[0]

#     # 
#     else:
#         res = supabase.table("tb_perchat").select("*").eq("perchat_id", "059f9863-a116-4590-bb8c-bdff476e7dde").execute()
#         return res.data[0]

#     # PAST MEMORY 불러오기
#     if e_data and "event_id" in e_data:
#         past_events = load_past_memory(e_data["event_id"], c_id)
#         past_memory_text = format_past_memory(past_events)
#         e_data["past_memory"] = past_memory_text
#     else:
#         e_data["past_memory"] = "(이전 기억이 없습니다.)"

#     return e_data
    


# print(load_all_event("TNMS00YJ00", as_yaml=True))

# 모든 이벤트 로드 -> yaml 형식
# chat_db_service.loaded_event_to_yaml(charac_id: str, as_yaml: bool = True):

# ✅ 4️⃣ 데이터 임베딩 후 VecDB 삽입 (컬렉션 없으면 생성)
# chat_vec_service.insert_events_to_vecdb(data: dict, collection_name:str="yujin_event"):

# 사건 데이터 로드
# data = chat_db_service.load_all_event(charac_id)
# 벡터 db에 업로드
# chat_vec_service.insert_events_to_vecdb(data, collection_name="yujin_event")

