# 系統架構（現況實錄 + 分析）

> 更新於 2026-07：已上線的 10 人 MVP。規模：後端 ~3,100 行 / 40 條路由 / 29 張表 /
> 40 測試 / 6 個 migrations；前端 ~820 行 / 8 頁。
> 擴容藍圖見 [SCALING.md](SCALING.md)；新增功能規範見 [PLAYBOOK.md](PLAYBOOK.md)。

## 1. 線上部署圖（現在真實在跑的）

```
使用者（瀏覽器/手機）
   │
   ▼
WEB  https://wei25-agent-social-web.hf.space     HF Docker Space（免費）
   │   Next.js 14 · port 3000 · 暱稱登入(localStorage→X-Dev-User)
   ▼  REST (fetch, CORS 白名單)
API  https://wei25-agent-social-api.hf.space     HF Docker Space（免費）
   │   FastAPI · port 8000 · 開機自動 alembic upgrade + seed
   ▼  SQLAlchemy (psycopg)
DB   Supabase Postgres（免費層）
       project ekwwvfjpfcpimladdnli · 走 transaction pooler
       aws-1-us-east-2.pooler.supabase.com:6543  ← 對北美用戶低延遲
```

- 部署方式：`deploy/hf_deploy.py`（upload_folder + secrets）。改完程式重跑即重新部署。
- 本機開發：`backend/ docker compose up`（Postgres+API）＋ `frontend/ npm run dev`。
- CI：GitHub Actions push/PR 跑 ruff + migration 驗證 + pytest（deploy 步驟目前跳過）。
- Secrets（API Space）：`DATABASE_URL`、`CORS_ORIGINS`、`ENVIRONMENT`；可選 `GEMINI_API_KEY`。
- 已知坑：DB 密碼 percent-encode 後，alembic env.py 需把 `%` 跳脫成 `%%`（已修）。

## 2. 程式分層（backend/app/）

```
api/        40 條路由（薄，只做驗證/權限/組裝）
services/   ★ 遊戲大腦：全部純函式、可單測、無框架依賴
models/     29 張表（SQLAlchemy）＋ alembic migrations
core/       config(env)、db session、auth、constants(軸/原型/白名單)
content/    scenarios.yaml 任務內容（填表上架，載入器冪等 upsert）
```

## 3. 三條核心資料流

### ① 靈魂管線（貼對話 → 小精靈）
```
POST /profiles/extract {text}
 → deid.scrub()            正則去識別化（email/電話/token/地址）— 原文不落庫
 → extraction.py           GEMINI_API_KEY 有→Gemini 2.5 Flash；無→規則版（關鍵字桶+訊號統計）
 → SelfExtractProfileIn    ★注入防線：數值 clamp 0-100、facet≤4、trait 白名單、未知欄位丟棄
 → facets.rank_facets()    依 weight 排序，切成多個 facet（一人多角）
 → generation.py           facet→原型(規則)→species→雷達(+原型加成再clamp)→層疊外觀→人設
 → characters 落庫（3-slot 上限）＋ moderation_queue
```
鐵則：**LLM 的輸出永遠不直接變成遊戲數字**，一律過 schema 驗證與伺服器端 clamp。

### ② 邂逅→朋友→聊天（社交主循環，模型 A：分身當媒人）
```
POST /characters/{id}/explore（每日 2 次）
 → 候選 = discoverable 且非自己且沒遇過的陌生小精靈
 → matchmaking.compatibility()  雷達cosine(0.5)+共同trait(0.25)+同facet(0.15)+互補(0.1)，權重可調
 → 取最高分 → character_chat.generate_chat()  短對話(3回合，模板/零LLM) + 一句摘要
 → GET /me/encounters  今日邂逅 digest（對方資料+契合+原因+摘要，主人身分隱藏）
 → POST /matches/{char_id}/wave  揮手 → 雙方互揮 → Friendship(accepted) 自動成立
 → /friends/{uid}/messages  私訊（輪詢、未讀數、僅限好友 403 gate）
```

### ③ 派遣任務（PvE 養成，data-driven）
```
content/scenarios.yaml（key/門檻/fail_above/synergy/台詞）
 → load_scenarios.py 冪等 upsert → POST /dispatches
 → resolver.resolve(chars, scenario, seed)  純確定性：同 seed 同結果
 → progression.apply_rewards()  xp/升級（只動 A 系統）
```

## 4. 關鍵設計決策（為什麼這樣蓋）

| 決策 | 內容 | 效益 |
|---|---|---|
| 雙帳本脫鉤 | A=養成數值(xp/level)、B=社群(獨特度/成就)互不寫入 | 防「刷強度霸社群榜」 |
| Data-driven | 雷達軸=`axes`表、任務=YAML、原型=表 | 加內容零程式零部署 |
| 純函式大腦 | resolver/compatibility/generate_chat 均為 (輸入,seed)→輸出 | 可測試、可重播、可快取 |
| 契約優先前端 | 後端維護 lib/api.ts+types+API.md+openapi.json，前端只消費 | 前後端並行不打架 |
| LLM 最小化 | 只在萃取(一次)用；對話/判定全模板+規則 | 10 人月成本 $0 |
| SVG 程式生成 | 頭像/雷達/卡＝確定性純函式 | 免圖床、可 CDN 快取 |
| 隱私前置 | 落庫前去識別化，原始對話不留存 | 合規負擔最小 |

## 5. 誠實的弱點清單（擴容前要還的債）

1. **配對/邂逅是 O(N) 全掃**：每次 explore/matches 撈全部候選算 cosine。百人無感，萬人會爆。解法=pgvector（見 SCALING）。
2. **暱稱即帳號**：`X-Dev-User` 無密碼，任何人可冒名。`core/security.py` 已留 Supabase JWT 路徑，換 auth 只動一處。
3. **聊天靠輪詢**（4 秒 poll）：百人可以，之後換 Supabase Realtime。
4. **免費層睡眠**：HF Space 48h 沒流量會睡（喚醒 ~30s）；Supabase 免費專案 7 天閒置會暫停。
5. **邂逅對話是罐頭模板**：靈魂體驗打折，設 GEMINI_API_KEY 可部分升級。
6. **部署是手動腳本**：`hf_deploy.py` 手跑，尚未接進 CI。
7. **無監控**：沒有錯誤追蹤/告警，掛了要自己發現。
