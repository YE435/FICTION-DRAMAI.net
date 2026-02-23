# # node/Dockerfile (개발용)
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci || npm install
COPY . .
CMD ["npm", "run", "dev"]

# FROM node:20-bullseye

# WORKDIR /app

# # 패키지 메타 먼저 복사(캐시)
# COPY package*.json ./

# # lockfile 있으면 ci, 없으면 install (감사/펀드 끔)
# RUN npm config set progress false \
#  && npm config set fund false \
#  && npm config set audit false \
#  && if [ -f package-lock.json ]; then npm ci; else npm install; fi

# # 앱 소스
# COPY . .

# # 필요하면 포트만 노출(예: 4000). 없어도 동작엔 문제 없음.
# # EXPOSE 4000

# # 프로젝트 스크립트에 맞게 선택
# # CMD ["npm", "run", "dev"]         # nodemon/ts-node 등 개발 모드
# CMD ["node", "server.js"]           # 또는 진입점 파일