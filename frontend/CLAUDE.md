# Frontend workspace — rules for editing

This folder (`ai-persona-game/frontend/`) is the **frontend redesign canvas**. You
may rebuild the UI however you like. Follow these rules so the backend keeps working.

## Hard rules
1. **Never edit the backend.** It lives in `../backend`. Treat it as a fixed API.
   If you need a new field/endpoint, write it down as a request — don't change
   `../backend` to match the UI.
2. **All backend calls go through `lib/api.ts`.** Don't scatter `fetch` calls or
   hardcode URLs in components. Add new endpoint wrappers there if needed.
3. **Types live in `lib/types.ts`** and mirror the backend. Keep them in sync;
   don't invent fields the API doesn't return.
4. The API contract is in **`API.md`** (human) and **`openapi.json`** (machine).
   Read those before adding features.

## Direction: lean (see ../ARCHITECTURE.md)
The plan is **Supabase for 80% (auth, CRUD, realtime chat, storage, admin) + a
thin FastAPI for the 20% brain (persona extraction, generation, matchmaking,
dispatch)**. Today everything goes through `lib/api.ts` → FastAPI; over time
auth/CRUD/chat move to the Supabase client. Don't hand-build infra the platform
gives for free. The FastAPI "smart" endpoints (/profiles, /matches, /dispatches,
/render) stay.

## The backend (already built & running)
- Base URL: `http://localhost:8000` (`NEXT_PUBLIC_API_URL`).
- Auth (dev): header `X-Dev-User: <name>` — already handled in `lib/api.ts`.
  Switch to Supabase `Authorization: Bearer` later by editing `authHeaders()` only.
- What exists: character generation, character CRUD, avatar/radar/card SVG
  rendering, friends, character sharing (friend + public link), and **dispatch
  quests** (`GET /scenarios`, `POST /dispatches` — deterministic, with growth).
  See `API.md`.
- NOT built yet (don't rely on): uniqueness leaderboard, achievements,
  conversation-export upload.

## Running
```bash
cp .env.local.example .env.local
npm install
npm run dev          # http://localhost:3000  (backend must be up on :8000)
```
Start the backend separately: `cd ../backend && docker compose up`.
> Backend CORS allows `localhost:3000` and `localhost:3001`. This frontend uses
> **3000**. The old prototype in `../frontend-web` is retired — don't run it.

## Suggested screens to design
- Onboarding / 生成角色（貼自我萃取 JSON 或問卷）
- 角色列表 + 角色詳情（頭像、雷達、個資料、改名、換外觀）
- 好友（加好友、邀請、列表）
- 分享（公開連結頁 `/shared/[token]`、分享給好友）

## Image helpers
`avatarUrl(id)`, `radarUrl(id)`, `cardUrl(id)`, `sharedCardUrl(token)` return public
SVG URLs you can drop straight into `<img src>` — no auth needed.
