# 功能開發規範（Playbook）— 新功能怎麼加、要守什麼規則

> 給未來的自己 / 任何協作的 AI：改這個 repo 前先讀這份。
> 架構事實見 [ARCHITECTURE.md](ARCHITECTURE.md)，擴容見 [SCALING.md](SCALING.md)。

## 一、十條鐵則（違反 = 埋雷）

1. **先問「Supabase/現成服務有沒有」**。80% 基建（auth/CRUD/即時/儲存/後台）不准手刻；
   FastAPI 只放 20% 大腦（萃取、生成、配對、判定、渲染）。
2. **LLM 輸出絕不直接變遊戲數字**。一律經 Pydantic schema 驗證 + 伺服器端
   clamp/白名單/strip（範本：`schemas/profile.py` + `services/facets.py`）。
3. **A/B 雙帳本不互寫**。養成數值(xp/level)不得影響社群分數，反之亦然。
4. **內容走資料，不走程式**。新任務=改 `content/scenarios.yaml`；新雷達軸=`axes` 表加一列；
   新原型=`archetypes` 表。若你發現在為「新內容」寫 Python，停下來重想。
5. **遊戲邏輯寫成純函式**放 `services/`：`(輸入, seed) → 輸出`，不碰 DB、不碰 request。
   route 只做權限/驗證/存取（範本：`resolver.py`、`matchmaking.py`）。
6. **凡是使用者觸發的寫入都要限流**（每日上限模式，見 explore/chat/friends 的 `_xxx_today()`）。
7. **隱私前置**：任何使用者原文在落庫/送 LLM 前先過 `deid.scrub()`；原始對話永不留存。
8. **migration 規矩**：既有表加 NOT NULL 欄位必須帶 `server_default`（否則線上炸，踩過）；
   migration 必須能在「空庫」與「有資料的庫」都跑過。
9. **契約同步**：後端 API 有變 → 必更新 `frontend/lib/api.ts`、`lib/types.ts`、`API.md`、
   重生 `openapi.json`。前端永遠不自己發明欄位。
10. **測了才算完成**：新功能至少「正常路 + 權限擋 + 限流擋」三個測試；`pytest` 綠 + `ruff` 淨才 push。

## 二、新增一個功能的標準流程（照抄即可）

以「送禮物給小精靈好友」為例：

```bash
cd backend && . .venv/bin/activate
```
1. **Model**：`app/models/` 加表（uuidpk + TimestampMixin），註冊進 `models/__init__.py`
2. **Migration**：
   ```bash
   export DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/persona_test
   make revision m="gifts"      # 自動生成，檢查產出的檔（鐵則8！）
   alembic upgrade head          # 空庫試跑
   ```
3. **Service**：`app/services/gifts.py` 純函式寫規則（誰能送、效果、限額）
4. **Schema + Route**：`app/schemas/` + `app/api/routes_gifts.py`（權限用 `get_current_user`，
   物件所有權自己查），掛進 `main.py`
5. **測試**：`tests/test_gifts.py`（正常/403/429），跑
   ```bash
   TEST_DATABASE_URL=...persona_testX pytest && ruff check .
   ```
6. **契約**：`make openapi`；補 `frontend/lib/api.ts`、`types.ts`、`API.md`
7. **前端**（可選）：`frontend/app/` 加 UI，只透過 `lib/api.ts` 拿資料
8. **上線**：
   ```bash
   git add -A && git commit && git push        # CI 自動驗證
   /opt/homebrew/anaconda3/bin/python3 deploy/hf_deploy.py   # 部署（容器開機自動跑 migration）
   ```

## 三、常見功能類型 → 對應套路

| 你想加的 | 套路 | 動哪裡 |
|---|---|---|
| 新任務/關卡 | 純內容 | 只改 `scenarios.yaml` → `make load-scenarios`，**零程式** |
| 新雷達軸/原型/外觀件 | registry | `axes`/`archetypes`/`avatar_parts` 表加列（可用 /ops 後台） |
| 新玩法規則（如天氣影響判定） | 純函式 | 只改 `resolver.py` + 測試 |
| 新社交互動（禮物/留言板） | 標準流程 | 上面 8 步全走，記得限流 |
| 新 LLM 能力（如邂逅對話升級） | 提供者模式 | 只改對應 service 的 `llm_provider` 分支；模板版必須保留當 fallback |
| 排行/統計類 | 批次 | 先寫「批次重算→存表→API 只讀」，別在請求路徑上現算 |
| 調參（權重/上限） | 設定 | `core/config.py` 加欄位（env 可覆蓋），別寫死在邏輯裡 |

## 四、Code Review 自問清單（push 前 30 秒）

- [ ] 這是不是在重造 Supabase 已有的輪子？
- [ ] 有沒有任何 LLM/使用者輸入未經 clamp 就進了數值欄位？
- [ ] 新寫入端點有每日/頻率限制嗎？
- [ ] migration 在有資料的庫上跑得過嗎（NOT NULL 有 default 嗎）？
- [ ] `pytest` + `ruff` 綠了嗎？openapi/types 同步了嗎？
- [ ] 這個查詢在 10,000 用戶時是 O(1)/索引查詢，還是全表掃？（是後者就先留 TODO 註記）
