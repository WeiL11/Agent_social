# Backend API 參考（前端契約）

Base URL：`http://localhost:8000`（設在 `NEXT_PUBLIC_API_URL`）。
互動式文件：http://localhost:8000/docs ｜ 機器可讀：[`openapi.json`](./openapi.json)。

> ⚠️ 這份是**契約**。後端在 `../backend`，**前端不要改後端**。需要新欄位/新端點 → 跟負責後端的人說，別自己改 schema。

## 認證

| 環境 | 怎麼帶身分 |
|---|---|
| Dev（目前） | header `X-Dev-User: <name>`，例如 `alice`。第一次呼叫會自動建帳號，handle = 該 name。 |
| 正式 | header `Authorization: Bearer <Supabase JWT>` |

公開端點（**免認證**）：所有 `GET /render/...`、`GET /shared/{token}`、`GET /shared/{token}/card.svg`、`GET /`、`GET /health`。其餘都要認證。

---

## 核心型別

**CharacterOut**
```ts
{ id, slot, name, species, archetype, facet,
  radar: Record<AxisId, number>,   // 0..100
  trait_tags: string[], persona, appearance: Record<string,string>,
  level, xp, status }              // status: "active" | "retired"
```
**AxisId（core 8）**：`logic` 邏輯 · `creativity` 創意 · `knowledge` 知識 · `curiosity` 好奇心 · `empathy` 同理 · `humor` 幽默 · `grit` 毅力 · `structure` 條理。（軸是 data-driven，未來可能增加。）

**有效 facet**：`coding` · `analytical` · `creative` · `social` · `learning` · `planning`。

---

## 端點

### 健康
- `GET /` → `{service,status,env}`
- `GET /health` → `{status, db}`

### 角色生成（核心流程）
`POST /profiles`（auth）— 貼性格側寫 → 依 facet 分群生成多隻角色（受 3-slot 上限）。
```jsonc
// body
{ "source": "self_extract",            // 或 "quiz"
  "apply_mode": "create_new",          // 或 "enrich_existing"
  "enrich_character_id": null,         // enrich 時必填
  "profile": {
    "version": "1.0",
    "facets": [
      { "facet": "coding", "weight": 80,
        "radar": { "logic": 85, "structure": 80 },  // 缺的軸自動補 50
        "trait_tags": ["systematic"], "species_hint": "robot",
        "summary": "愛拆解問題" }
    ],
    "overall_summary": "..." }
}
// → GenerateResult
{ "created": CharacterOut[], "skipped_facets": string[], "slot_cap": 3 }
```
注意：數值會被 server clamp 到 0–100、trait 過白名單、PII 會被清，facet 上限 4。

### 角色
- `GET /characters`（auth）→ `CharacterOut[]`（自己的，依 slot 排序）
- `GET /characters/{id}`（auth）→ `CharacterOut`
- `PUT /characters/{id}`（auth）body `{ name?, appearance? }` → `CharacterOut`（改名/換外觀，**cosmetic，不動數值**）
- `PUT /characters/{id}/appearance`（auth）body `{ appearance }` → `CharacterOut`

### 形象 / 雷達 / 角色卡（公開 SVG，可直接 `<img src>`)
- `GET /render/characters/{id}/avatar.svg` → 層疊頭像
- `GET /render/characters/{id}/radar.svg` → 8 軸雷達
- `GET /render/characters/{id}/card.svg` → 合成角色卡（頭像+雷達+個資料）

### 派遣任務（#3，純規則判定）
- `GET /scenarios`（auth）→ `Scenario[]`：`{ id, title, type, requirements, rewards }`
- `POST /dispatches`（auth）body `{ scenario_id, character_ids: string[], seed? }` → `DispatchResult`
  ```jsonc
  // DispatchResult
  { "dispatch_id": "...", "outcome": "success" | "fail",
    "log": { "steps": [...], "text": "敘事文字", "margin": 12, "roll": 3 },
    "rewards": { "xp": 100 },
    "characters": CharacterOut[] }   // 成功時 xp/level 已更新（A 系統成長）
  }
  ```
  判定純規則：隊伍各軸取最佳值 → 比對 `requirements.min` 門檻、`fail_above` 過高自動失敗、
  `synergy_traits` 命中加成、seed 控制隨機。同 seed 同結果（可重播）。

### 好友（兩種層級）

**A. 飼主好友（user ↔ user，一般加好友，上限 100）**
- `POST /friends/requests`（auth）body `{ handle }` → `FriendOut`
- `GET /friends`（auth）→ `FriendOut[]`
- `POST /friends/requests/{friendship_id}/accept`（auth）→ `FriendOut`
- `DELETE /friends/requests/{friendship_id}`（auth）→ `{deleted}`
- `GET /friends/{friend_user_id}/characters`（auth）→ `CharacterOut[]`
  ← 飼主好友福利：看到**那個人管理的全部小精靈**（非好友 → 403）

**FriendOut**：`{ friendship_id, user_id, handle, status, direction }`
direction：`incoming` / `outgoing` / `friends`。超過 100 → 409。

**B. 小精靈好友（character ↔ character，每隻每天限交 2 個）**
- `POST /characters/{character_id}/friends`（auth）body `{ target_character_id }` → `CharacterFriendResult`
  `{ friend: CharacterOut, remaining_today }`。超過每日上限 → **429**。
- `GET /characters/{character_id}/friends`（auth）→ `CharacterOut[]`
  ← **只露出另一隻小精靈**（看不到對方飼主或其 roster）
- `DELETE /characters/{character_id}/friends/{other_character_id}`（auth）→ `{deleted}`

### 分享
- `POST /characters/{id}/share`（auth）body `{ target }` → `ShareOut`
  - `target: "public"` → 公開連結；`target: "<friend_user_id>"` → 分享給好友（須為 accepted 好友，否則 403）
  - `ShareOut`：`{ token, is_public, url, card_url }`
- `GET /shared/{token}`（公開）→ `SharedCharacterOut`：`{ name, species, archetype, radar, trait_tags, persona, level, owner_handle }`
- `GET /shared/{token}/card.svg`（公開）→ 角色卡圖
- `GET /shared`（auth）→ `SharedCharacterOut[]`（好友分享給我的）

### 運營後台（需 admin 角色，一般玩家會拿到 403）
- `GET /admin/health` · `GET /admin/moderation?status_filter=pending` · `POST /admin/moderation/{item_id}?decision=approved|rejected`

---

## 典型前端流程
1. （冷啟動）讓使用者貼自我萃取 JSON → `POST /profiles` → 拿到 `created` 角色。
2. 列表頁 `GET /characters`，每隻用 `/render/.../avatar.svg`、`card.svg` 顯示。
3. 詳情頁可改名 `PUT /characters/{id}`。
4. 好友頁：`GET /friends` + `POST /friends/requests` + accept/delete。
5. 分享：`POST /characters/{id}/share` → 拿 `url`/`card_url` 給使用者複製；公開頁讀 `GET /shared/{token}`。
