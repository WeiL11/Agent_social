# 精簡架構（別重造輪子）

決策：**FastAPI 只做「20% 護城河」的運算；80% 通用基建全交給 Supabase。**
不重寫已存在的東西（能跑就先放著），但**從現在起新功能不再手刻基建**。

## 目標架構

```
            ┌─────────────────────────────────────────────┐
 Frontend ─►│ Supabase（設定，非手刻程式）                    │
 (Next.js)  │  Auth · Postgres · 自動 REST(PostgREST)+RLS    │
            │  Realtime(聊天) · Storage · Table Editor(後台)  │
            └───────────────┬─────────────────────────────┘
                            │ 同一個 Postgres
 Frontend ─► FastAPI（我維護，只放「不能純 CRUD」的腦）
             /profiles   性格萃取 → facet → 角色生成(注入防護/clamp)
             /matches    契合度配對演算法
             /dispatches 派遣判定 + 成長
             /render     角色卡 SVG（你的美術邏輯）
             /load-scenarios 任務內容載入
```

兩條存取路徑共用 **同一個 Supabase Postgres**：日常讀寫走 Supabase 自動 API，
需要運算/防作弊的走 FastAPI。

## 誰做什麼（分工）

| 層 | 負責 | 內容 |
|---|---|---|
| **Supabase** | 你（設定） | Auth、資料表、RLS 權限、Realtime 聊天、Storage、Table Editor 當後台 |
| **FastAPI（20% 腦）** | 我 | 性格萃取、角色生成(clamp/白名單/PII)、配對、派遣判定、SVG、內容載入 |
| **Frontend** | 你 + 另一個 Claude | UI；用 Supabase client 拿 auth/CRUD/聊天，呼叫 FastAPI 做那 4 件聰明事 |

## 已建程式碼的歸類（不急刪，但標記）

**保留（= 護城河，FastAPI 該做的）**
- `services/generation.py`、`services/facets.py`、`services/deid.py`（萃取+生成+防護）
- `services/matchmaking.py`、`routes_matches.py`（配對）
- `services/resolver.py`、`services/progression.py`、`routes_dispatch.py`（派遣）
- `services/svg.py`、`routes_render.py`（角色卡）
- `content/scenarios.yaml` + `load_scenarios.py`（任務內容產線）

**之後由 Supabase 取代（= 輪子，先放著、別再擴充）**
- `core/security.py`（X-Dev-User/JWT stub）→ **Supabase Auth**
- `routes_characters.py` 的列表/讀取、`routes_me.py`、`routes_social.py` 的 CRUD → **PostgREST + RLS**
- `routes_messages.py`（輪詢 DM）→ **Supabase Realtime**
- `admin_ui.py`（sqladmin）、`routes_admin.py` → **Supabase Table Editor**

## 漸進遷移（無急迫、不停機）

1. 現在：一切照常用 FastAPI，不會壞。
2. 接 **Supabase Auth**：前端改用 Supabase 登入 → JWT；FastAPI 既有的 JWT 驗證接上即可（`core/security.py` 已預留）。
3. 簡單讀取改走 **Supabase client**（PostgREST），逐步把 `GET /characters` 等從前端改成直連。
4. 聊天改 **Realtime**，丟掉輪詢 DM。
5. 後台用 **Table Editor**，下架 sqladmin。

## 鐵則
- **防作弊/運算邏輯永遠留在 FastAPI**（生成 clamp、配對、判定），不可變成純 CRUD。
- 新功能先問：「Supabase 有現成嗎？」有就用，沒有才寫 FastAPI。
