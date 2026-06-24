# AI Persona Game — Frontend (redesign canvas)

A clean Next.js + TypeScript app to (re)design the UI against a fixed backend.
The backend is already built and running in `../backend`; **this folder never
modifies it**.

## Quick start
```bash
cd ../backend && docker compose up -d   # backend on :8000 (if not already up)
cd ../frontend
cp .env.local.example .env.local
npm install
npm run dev                              # http://localhost:3000
```

## What's here
| File | Purpose |
|---|---|
| `lib/api.ts` | Typed client — the only place that calls the backend |
| `lib/types.ts` | TypeScript types mirroring the API |
| `lib/sample.ts` | Sample profile fixture for testing generation |
| `API.md` | Human-readable endpoint reference (the contract) |
| `openapi.json` | Machine-readable OpenAPI spec |
| `CLAUDE.md` | Rules for editing (read this first) |
| `app/` | Pages — `app/page.tsx` is a blank starter, redesign freely |

## The deal
- Build any UI you want under `app/` and components.
- Use `lib/api.ts` for data; read `API.md` for what's available.
- Don't touch `../backend`. Need an API change? Note it and ask.

The old prototype `../frontend-web` is retired (it used :3000 too) — this folder
replaces it. You can delete `frontend-web` once you're happy here.
