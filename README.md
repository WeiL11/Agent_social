# AI Persona Game

「你的 AI 對話，會長成你的角色。」一款以角色養成為核心的遊戲——角色由玩家與
Claude / ChatGPT / Gemini 對話的性格萃取生成。完整設計見
`~/.claude/plans/claude-ai-rustling-shamir.md`。

這是 **階段 1：可運行的後端骨架 + API 優先架構**（同一套 REST API 同時供網站與未來的手機 App）。

## 架構

```
frontend-web/  Next.js 網站 (Vercel)        ┐
(future) app/  Expo / React Native 手機 App ┘── 都打同一套 REST API
backend/       FastAPI + Postgres (Supabase) — 唯一資料入口
```

- **API 優先**：所有遊戲邏輯在 backend；前端只是 client。要做 App 時新增一個 Expo 專案、
  沿用 `backend` 的 REST API 即可（只需換 `lib/api.ts` 的 base URL 與 auth 來源）。
- 設計取捨見計畫：LLM 僅冷啟動、任務純規則、雙價值系統脫鉤、雷達軸 data-driven。

## 快速啟動

### 後端（Docker，一鍵）
```bash
cd backend
docker compose up --build
# API: http://localhost:8000  ·  互動式文件: http://localhost:8000/docs
```
啟動時會自動建表並 seed（core 8 雷達軸、原型、範例任務）。

### 後端（本機 Python，不用 Docker）
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 指向你的本機 Postgres
python -m app.init_db         # 建表 + seed
uvicorn app.main:app --reload
```

### 前端網站
```bash
cd frontend-web
cp .env.local.example .env.local
npm install
npm run dev                    # http://localhost:3000
```

## 試一次完整流程
1. 開 http://localhost:3000
2. 直接用預填的「自我萃取側寫 JSON」按 **生成角色**
3. 下方會出現依 facet 生成的角色（受 3-slot 上限）

或用 API：
```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/profiles -H 'Content-Type: application/json' \
  -H 'X-Dev-User: alice' \
  -d '{"source":"self_extract","apply_mode":"create_new","profile":{"version":"1.0","facets":[{"facet":"coding","weight":80,"radar":{"logic":85,"structure":80},"trait_tags":["systematic"],"species_hint":"robot","summary":"愛拆解問題"}]}}'
curl -s localhost:8000/characters -H 'X-Dev-User: alice'
```

## 認證
- **Dev**：沒設 `SUPABASE_JWT_SECRET` 時，用 `X-Dev-User` header 當身分（前端已內建）。
- **正式**：設 `SUPABASE_JWT_SECRET`，前端改送 `Authorization: Bearer <supabase jwt>`。

## 運營後台
MVP 用 **Supabase Table Editor** 看資料 + 內建 `/admin/*` API（moderation queue）。
之後接 sqladmin 或自建 Next.js admin。Admin API 與玩家 API 權限分離。

## 資料夾
- `backend/` — FastAPI + Postgres（**我/後端負責**）
- `frontend/` — Next.js 重構畫布（**你+另一個 Claude 負責**，:3000）。契約見 `frontend/API.md`
- `frontend-web/` — 舊原型，已退役

## 目前實作了什麼
- ✅ 完整資料模型（A 養成 / B 社群 / 運營後台 三組表）+ data-driven 雷達軸 registry
- ✅ 攝取→facet 分群→規則生成角色（注入防護：clamp / 白名單 / PII 去識別 / 3-slot 上限）
- ✅ 角色 CRUD、改名、外觀編輯（cosmetic 與數值脫鉤）
- ✅ 角色形象/雷達/角色卡 SVG 渲染；好友 + 分享（好友 / 公開連結）
- ✅ **#3 派遣任務**：`GET /scenarios`、`POST /dispatches`（純規則確定性判定 + 成長）
- ✅ Auth（Supabase JWT + dev fallback）、admin moderation
- ✅ **工程地基**：pytest（19 測試）、ruff、Alembic migrations、CI/CD（GitHub Actions → Fly.io）
- ⏳ 之後：#2 社群獨特度/排行、achievements、export adapters、Expo App

## 後端開發（CI/CD-ready）
```bash
cd backend
make install                 # venv: pip install -r requirements-dev.txt
make lint                    # ruff
TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/persona_test make test
make revision m="msg"        # autogenerate a migration
make migrate                 # alembic upgrade head
make openapi                 # 重新匯出 frontend/openapi.json 契約
```
- **CI**：push/PR → lint + 驗證 migrations 能套用 + pytest（`.github/workflows/ci.yml`）。
- **CD**：push 到 `main` 且 CI 通過 → `flyctl deploy`（需 repo secret `FLY_API_TOKEN`）。
- **部署前**：`fly launch --no-deploy`、`fly secrets set DATABASE_URL=... SUPABASE_JWT_SECRET=... CORS_ORIGINS=...`（見 `backend/fly.toml`）。
- 容器啟動會自動 `alembic upgrade head && python -m app.seed`，所以加新功能 = 寫 model→`make revision`→push，CI/CD 自動帶上線。
