# AI Studio Build — 貼上用 Brief（前端重做/美化）

把整份貼進 Google AI Studio 的 **Build** 提示框，請它生一個 **React（client-side）** 應用。
重點：**先用內建假資料（mock）做出可運作的 UI**，之後把 `API_BASE` 換成已部署的後端網址即可接上真資料。
（AI Studio 預覽跑在雲端沙箱，連不到本機 `localhost:8000`，所以一定要先 mock。）

---

## 產品一句話
「你的 AI 對話，會長成你的小精靈。」養成牠、看牠和別的小精靈短聊，並用牠的性格幫你**配對到合得來的真人**。

## 技術要求
- React（AI Studio 預設即可），單一 SPA、用 React Router 分頁。
- 建一個 `api.ts`：頂部有 `const API_BASE = ""`（空字串時走 mock）與 `const USE_MOCK = true`。
  所有資料存取都透過這裡；之後把 `API_BASE` 設成後端網址、`USE_MOCK=false` 就接真後端。
- 視覺風格：可愛又有點科技感，圓角、柔和紫色系（主色 `#6b4eff`），卡片式。手機優先 RWD。

## 7 個畫面（路由 + 內容 + 對應 API）
1. **首頁 `/`**：第一次無角色時顯示歡迎引導；否則顯示「我的角色」網格（頭像+名字+等級）。有「＋新增角色」面板（貼自我萃取 JSON → 生成）。 API: `GET /characters`、`POST /profiles`。
2. **角色詳情 `/character/:id`**：角色卡（頭像+雷達圖+人設+特質）、改名；「小精靈的朋友」列表（每天可交 2 個）；「對話紀錄」（短對話 + 摘要，可看全文）。 API: `GET /characters/:id`、`GET/POST /characters/:id/friends`、`GET/POST /characters/:id/chats`。
3. **配對/朋友 `/friends`**：配對推薦（對方角色卡 + 契合度分數 + 原因 + 揮手）；我的朋友列表（加好友、接受、進聊天）。 API: `GET /matches`、`POST /matches/:id/wave`、`GET /friends`、`POST /friends/requests`。
4. **私訊聊天室 `/chat/:friendUserId`**：訊息泡泡 + 輸入框（輪詢更新）。 API: `GET/POST /friends/:id/messages`。
5. **設定 `/settings`**：「可被配對」開關、顯示 handle。 API: `GET/PUT /me`。
6. **公開分享頁 `/shared/:token`**：免登入看某角色卡。 API: `GET /shared/:token`。
7. **派遣任務 `/quests`（可選）**：任務列表 + 派角色出任務看結果。 API: `GET /scenarios`、`POST /dispatches`。

## TypeScript 型別（照這個 shape 做 UI / mock）
```ts
type Radar = Record<string, number>; // axes: logic creativity knowledge curiosity empathy humor grit structure (0..100)
interface Character { id:string; name:string|null; species:string|null; archetype:string|null;
  facet:string|null; radar:Radar; trait_tags:string[]; persona:string|null;
  appearance:Record<string,string>; level:number; xp:number; status:string }
interface Match { their_character:Character; my_character_id:string; score:number; reasons:string[]; waved:boolean }
interface Friend { friendship_id:string; user_id:string; handle:string; status:string; direction:"incoming"|"outgoing"|"friends" }
interface DirectMessage { id:string; from_me:boolean; body:string; created_at:string; read:boolean }
interface CharacterChat { id:string; transcript:{speaker:string;text:string}[]; summary:string|null; created_at:string }
interface Me { handle:string; discoverable:boolean }
```

## Mock 資料（USE_MOCK 時用）
```ts
const MOCK_CHARACTERS: Character[] = [
  { id:"c1", name:"創作者", species:"sprite", archetype:"artist", facet:"creative",
    radar:{logic:55,creativity:90,knowledge:70,curiosity:80,empathy:55,humor:60,grit:50,structure:65},
    trait_tags:["curious","imaginative"], persona:"【創作者】天馬行空愛玩點子",
    appearance:{body:"sprite"}, level:1, xp:0, status:"active" },
  { id:"c2", name:"分析者", species:"robot", archetype:"analyst", facet:"coding",
    radar:{logic:90,creativity:50,knowledge:70,curiosity:60,empathy:50,humor:50,grit:55,structure:80},
    trait_tags:["systematic"], persona:"【分析者】愛拆解問題", appearance:{body:"robot"},
    level:2, xp:120, status:"active" },
];
const MOCK_MATCHES: Match[] = [
  { their_character: MOCK_CHARACTERS[0], my_character_id:"c2", score:90,
    reasons:["都有「創作」分身","共同特質：curious","都很強：創意、好奇心"], waved:false },
];
const MOCK_FRIENDS: Friend[] = [{ friendship_id:"f1", user_id:"u9", handle:"kai", status:"accepted", direction:"friends" }];
const MOCK_MESSAGES: DirectMessage[] = [
  { id:"m1", from_me:false, body:"嗨！我們配對成功了 🎉", created_at:"", read:true },
  { id:"m2", from_me:true, body:"對啊，你也喜歡寫程式？", created_at:"", read:true },
];
const MOCK_CHAT: CharacterChat = { id:"cc1", summary:"創作者 和 分析者 聊了創作與程式，氣氛一拍即合。", created_at:"",
  transcript:[{speaker:"分析者",text:"嗨 創作者！我最近都在玩程式。"},{speaker:"創作者",text:"我比較常碰創作～"}] };
```
角色頭像/角色卡圖：mock 階段用 emoji 或色塊占位；接真後端後改用
`${API_BASE}/render/characters/:id/avatar.svg`（與 `/card.svg`）當 `<img src>`。

## 之後接真後端（部署後）
1. 後端部署到公開網址（例：Fly.io）→ 拿到 `https://xxx`。
2. AI Studio 程式裡設 `API_BASE="https://xxx"`、`USE_MOCK=false`。
3. 認證：dev 用 header `X-Dev-User: <name>`；正式換成 `Authorization: Bearer <Supabase JWT>`。
4. 完整端點與 shape 見本 repo 的 `frontend/API.md` 與 `frontend/openapi.json`（也可一起貼給 AI Studio）。

## 給 AI Studio 的指示語（可直接用）
> 用 React 做上述 7 個畫面的 SPA，先用內建 mock 資料讓每頁可運作，所有資料存取集中在 `api.ts`
> 並用 `API_BASE`/`USE_MOCK` 控制；風格走可愛＋科技感、主色 #6b4eff、卡片式、手機優先。
