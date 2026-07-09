# 擴容藍圖：北美用戶 10 → 100 → 10,000 在線

> 原則：**資料永遠在 Postgres（Supabase），運算層無狀態** → 擴容 = 換更大的殼，
> 資料不搬家。DB 已在 us-east-2，對北美天然低延遲，此優勢每一階段都保留。
> 「在線」= 同時活躍連線（concurrent）。10k 在線 ≈ 十萬級註冊用戶，是認真規模。

## 階段 0：現在（≤10 穩定在線）— $0/月

現況即可。兩件小事別踩雷：
- **Supabase 免費專案閒置 7 天會暫停** → 測試期保持有人用，或每天 cron ping `/health`。
- HF Space 48h 睡眠 → 告訴朋友「第一次開要等 30 秒」。

## 階段 1：100 穩定在線 — 約 $35–60/月

100 併發對單台 FastAPI + Postgres 是輕鬆的；這一階段的重點**不是效能，是「可靠 + 可信」**：

| 事項 | 做法 | 為什麼 |
|---|---|---|
| ① 真帳號 | 接 Supabase Auth（後端 JWT 驗證已寫好，設 `SUPABASE_JWT_SECRET`；前端換 supabase-js 登入） | 暱稱可冒名，100 陌生人不行 |
| ② 不睡眠 | Supabase Pro $25 + API 搬 Fly/Railway 常駐小機($5-10)，或 HF 付費常駐硬體 | 冷啟動勸退新用戶 |
| ③ 自動部署 | 把 `hf_deploy.py`（或 flyctl）接進 GitHub Actions，push=上線 | 手動部署會漏 |
| ④ 監控 | Sentry 免費層 + UptimeRobot ping | 掛了要先於用戶知道 |
| ⑤ 全域限流 | slowapi per-IP/per-user rate limit | 現在只有玩法限流，沒有 API 限流 |
| ⑥ 索引體檢 | characters(owner_id)、messages(to,read_at)、chats(created_at) 等熱查詢加索引 | 便宜的保險 |

**不需要做**：Redis、多實例、pgvector——都還早。

## 階段 2：1,000 在線 — 約 $150–300/月（過渡站）

- API 開 **2–3 個無狀態副本** + 平台自帶 LB（Fly `scale count 3` 一行）。
- **配對改 pgvector**（關鍵債，見下）。
- 聊天輪詢 → **Supabase Realtime**（DM 表已在 Supabase，前端訂閱即可，後端不用改）。
- 加 **Redis**：排行榜 sorted set、每日限額計數、熱資料快取。
- 背景工作獨立（RQ worker）：邂逅批次、population_stats 重算。

## 階段 3：10,000 在線 — 約 $500–1,500/月

```
Cloudflare CDN/WAF
   ├─ 前端：Vercel/Pages（北美邊緣節點）
   ├─ /render/*.svg：確定性輸出 → CDN 長快取（Cache-Control: immutable）
   ▼
API × 5–15 無狀態副本（Fly us-east autoscale / Cloud Run）
   ├─ Redis（快取/限流/佇列）
   ├─ Worker 群（RQ）：邂逅預算批次、摘要、獨特度、事件結算
   ▼
Supabase Postgres：dedicated compute（4–8C）＋ read replica（讀寫分離）
   └─ pgvector HNSW 索引：配對/邂逅候選 = 毫秒級 ANN 查詢
```

各瓶頸的對策：

| 瓶頸 | 對策 |
|---|---|
| **配對 O(N) 全掃**（最大殺手） | `characters.radar` 同步存 `vector(8)` 欄位 + HNSW 索引；候選=`ORDER BY embedding <=> :me LIMIT 50` 再過濾精算。另把「每日邂逅」改成**離線批次預算**（worker 半夜算好，白天只讀），尖峰 CPU 歸零 |
| DB 連線耗盡 | 已走 Supavisor transaction pooler（可撐 10k+ 併發）；副本數 × pool size 控制在池限的 40% |
| 聊天 fan-out | Supabase Realtime 分級配額；再大才考慮專用 WS 服務（Stream/Ably） |
| SVG 渲染 CPU | CDN 快取後源站幾乎零負載（同角色同輸出） |
| LLM 成本（若邂逅接了 Gemini） | 只生一次存庫（現有設計）＋ 摘要快取；絕不做「每次瀏覽都生成」 |
| 熱資料 | 排行榜/population_stats 進 Redis，5 分鐘重算一次 |

### 遷移不痛的原因（現在的設計紅利）
- API 無狀態 → 加副本不改碼；純函式大腦 → 可搬進 worker 不改碼；
- 契約優先 → 換 host 只改前端 `API_BASE` 一個值；
- 資料自始至終在同一個 Supabase，**零遷移**。

### 何時觸發下一階段（訊號，不看感覺）
- p95 API 延遲 > 500ms 持續一週 → 加副本
- `/matches`、`/explore` 單次 > 300ms → 上 pgvector
- DB CPU > 60% 持續 → 升 compute / read replica
- Realtime 併發逼近方案配額 → 升級或外掛 WS
