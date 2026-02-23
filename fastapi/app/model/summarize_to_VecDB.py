#!/usr/bin/env python
# coding: utf-8

# In[3]:


import os
from dotenv import load_dotenv
from supabase import create_client, Client
import time, uuid

# .env 경로 지정 # /fastapi/.env
load_dotenv("../../.env")  # /fastapi/app/model 기준 상대경로

# Supabase 연결
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

print("URL:", os.getenv("SUPABASE_URL"))
print("KEY:", os.getenv("SUPABASE_ANON_KEY")[:6], "...")

openai_key = os.getenv("OPEN_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_key

import sys
import os
# 현재 작업 디렉토리 확인
print("현재 작업 디렉토리:", os.getcwd())

# fastapi 루트를 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)


# In[45]:


from app.services.script_service import list_scripts
from app.db import supabase

def list_all_scripts():
    all_data = []
    offset = 0
    chunk_size = 1000

    while True:
        res = (
            supabase.table("tb_script")
            .select("*")
            .range(offset, offset + chunk_size - 1)
            .execute()
        )

        # 데이터 없으면 끝내기
        if not res.data:
            break

        all_data.extend(res.data)
        offset += chunk_size

    print(f"총 {len(all_data)}개 데이터 로드 완료")
    return all_data
all_data = list_all_scripts()
all_data


# In[5]:


from collections import defaultdict

def group_by_episode(data: list):
    episodes = defaultdict(list)

    for d in data:
        if not d.get("episode_no"):
            continue  # episode_no 없는 데이터는 제외
        episodes[d["episode_no"]].append(d)

    print(f"✅ 총 {len(episodes)}개의 에피소드로 그룹핑 완료")
    return episodes

episode = group_by_episode(data)
episode[1]


# In[6]:


from collections import defaultdict

def group_scene_in_episode(episode_dict: dict):
    ep_scene_dict = {}

    for ep_no, scripts in episode_dict.items():
        scenes = defaultdict(list)

        for d in scripts:
            if not d.get("scene_no"):
                continue
            scenes[d["scene_no"]].append(d)

        # 씬별로 script_no 순서대로 정렬
        for scene_no in scenes:
            scenes[scene_no] = sorted(scenes[scene_no], key=lambda x: x["script_no"])

        ep_scene_dict[ep_no] = scenes

    print(f"✅ 총 {len(ep_scene_dict)}개의 에피소드에서 씬 그룹핑 완료")
    return ep_scene_dict


# In[36]:


scene = group_scene_in_episode(episode)
scene[1][1]


# In[27]:


# LLM
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    model='gpt-4.1-mini',
    max_token='512',
    temperature=0.3,
)
# 임베딩
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embedding_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# In[40]:


episode_no = 1  
scene_no = 1    

data_1 = scene[episode_no][scene_no]

script_ids = [d["script_no"] for d in data_1]
combined_text = "\n".join(
    [f"{d['speaker']}: {d['dialogue']}" 
     for d in data if d.get("dialogue")]
)

print(combined_text)
print(f"script_no : {script_ids}")
print(data_1)


# In[25]:


# 1화의 씬 번호 목록
scene_nos = [d["scene_no"] for d in episode[1] if d.get("scene_no")]

# 중복 제거
unique_scenes = set(scene_nos)

# 출력
print(f"🎬 1화의 씬 개수: {len(unique_scenes)}개")
print(f"씬 번호 목록: {sorted(unique_scenes)}")


# In[26]:


# 벡터DB
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext, VectorStoreIndex

qdrant_client = QdrantClient(
    host="localhost",
    port="6333"
)
print(qdrant_client.get_collections())


# In[47]:


from collections import defaultdict

def build_scene_dict(data: list):
    """
    🎬 대본 전체 데이터를 episode_no → scene_no 단위로 그룹핑
    결과: { episode_no: { scene_no: [ {...}, {...}, ... ] } }
    """
    # 에피소드별 그룹핑
    episode_dict = defaultdict(list)
    for d in data:
        if not d.get("episode_no"):
            continue
        episode_dict[d["episode_no"]].append(d)

    # 에피소드 내 씬별 그룹핑
    scene_dict = {}
    for ep_no, scripts in episode_dict.items():
        scenes = defaultdict(list)
        for d in scripts:
            if not d.get("scene_no"):
                continue
            scenes[d["scene_no"]].append(d)

        # 각 씬을 script_no 기준으로 정렬
        for sc_no in scenes:
            scenes[sc_no] = sorted(scenes[sc_no], key=lambda x: x["script_no"])

        scene_dict[ep_no] = scenes

    print(f"✅ 총 {len(scene_dict)}개의 에피소드에서 씬 그룹핑 완료")
    return scene_dict
scene_dict = build_scene_dict(all_data)


# In[50]:


from qdrant_client.models import VectorParams, Distance
import uuid, time
from tqdm import tqdm

def create_script_sum_collection(collection_name="script_sum"):
    if collection_name not in [c.name for c in qdrant_client.get_collections().collections]:
        dim = embedding_model._model.get_sentence_embedding_dimension()
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={collection_name: VectorParams(size=dim, distance=Distance.COSINE)},
        )
        print(f"✅ 새 컬렉션 생성: {collection_name}")
create_script_sum_collection();
total_count = 0

# 2️⃣ 에피소드별 반복
for ep_no, scenes in tqdm(scene_dict.items(), desc="📺 Episode 진행중"):
    for sc_no, scripts in scenes.items():

        # 🔹 2-1. 대사 합치기
        combined_text = "\n".join(
            [f"{d['speaker']}: {d['dialogue']}" for d in scripts if d.get("dialogue")]
        )
        if not combined_text.strip():
            continue

        # 🔹 2-2. script_id 리스트
        script_ids = [d["script_id"] for d in scripts if d.get("script_id")]

        # 🔹 2-3. LLM으로 요약 생성
        prompt = f"""
        다음은 드라마의 한 씬 대사입니다.
        이 씬의 핵심 내용과 감정의 흐름을 한 줄로 요약해줘.

        {combined_text}
        """

        try:
            res = llm.complete(prompt)
            summary_text = res.text if hasattr(res, "text") else str(res)
        except Exception as e:
            print(f"⚠️ LLM 요약 실패 (Episode {ep_no}, Scene {sc_no}): {e}")
            continue

        # 🔹 2-4. 요약문 임베딩
        summary_vec = embedding_model.get_text_embedding(summary_text)

        # 🔹 2-5. payload 구성
        payload = {
            "episode_no": ep_no,
            "scene_no": sc_no,
            "script_ids": script_ids,
            "script_summary": summary_text,
            "ts": time.time()
        }

        # 🔹 2-6. Qdrant 업서트
        qdrant_client.upsert(
            collection_name="script_sum",
            points=[{
                "id": str(uuid.uuid4()),
                "vector": {"script_summary": summary_vec},
                "payload": payload
            }]
        )

        total_count += 1

print(f"\n✅ 총 {total_count}개의 씬 요약 임베딩 완료 및 Qdrant 저장됨!")


# In[ ]:




