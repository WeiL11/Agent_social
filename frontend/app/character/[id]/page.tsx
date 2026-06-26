"use client";

import { useEffect, useState } from "react";
import {
  befriendCharacter, cardUrl, getCharacter, getCharacterChat, listCharacterChats,
  listCharacterFriends, startCharacterChat, updateCharacter,
} from "../../../lib/api";
import type { Character, CharacterChat, CharacterChatSummary } from "../../../lib/types";

export default function CharacterPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [c, setC] = useState<Character | null>(null);
  const [friends, setFriends] = useState<Character[]>([]);
  const [chats, setChats] = useState<CharacterChatSummary[]>([]);
  const [openChat, setOpenChat] = useState<CharacterChat | null>(null);
  const [targetId, setTargetId] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    try {
      setC(await getCharacter(id));
      setFriends(await listCharacterFriends(id));
      setChats(await listCharacterChats(id));
    } catch (e: any) { setErr(e.message); }
  }
  useEffect(() => { load(); }, [id]);

  if (!c) return <main className="container"><p className="muted">{err || "載入中…"}</p></main>;

  return (
    <main className="container">
      <a href="/" className="muted">← 我的角色</a>

      {/* Display + 說明 */}
      <div className="card">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={cardUrl(id)} alt="card" style={{ width: "100%", maxWidth: 480, borderRadius: 12 }} />
        <h2>{c.name}</h2>
        <div className="muted">{c.archetype} · {c.species} · facet={c.facet} · Lv{c.level}（xp {c.xp}）</div>
        <p>{c.persona}</p>
        <div>{(c.trait_tags || []).map((t) => <span key={t} className="pill">{t}</span>)}</div>
        <button className="ghost" onClick={async () => {
          const n = prompt("改名：", c.name ?? ""); if (n) { await updateCharacter(id, { name: n }); load(); }
        }}>改名</button>
      </div>

      {/* 角色好友 */}
      <div className="card">
        <h3>小精靈的朋友（{friends.length}）</h3>
        <p className="muted">每隻每天可交 2 個。輸入對方角色 ID 來交朋友（之後前端可換成從配對點擊）。</p>
        <div className="row">
          <input value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="對方 character id" />
          <button onClick={async () => {
            setErr("");
            try { await befriendCharacter(id, targetId.trim()); setTargetId(""); load(); }
            catch (e: any) { setErr(e.message); }
          }}>交朋友</button>
        </div>
        <ul>{friends.map((f) => <li key={f.id}>{f.name}（{f.archetype}） <button className="ghost"
          onClick={async () => { setOpenChat(await startCharacterChat(id, f.id)); load(); }}>發起對話</button></li>)}</ul>
      </div>

      {/* 角色對話 + 摘要 */}
      <div className="card">
        <h3>對話紀錄</h3>
        {chats.length === 0 && <p className="muted">還沒有對話。跟一個小精靈朋友「發起對話」吧。</p>}
        <ul>{chats.map((ch) => <li key={ch.id}>
          📝 {ch.summary} <button className="ghost"
            onClick={async () => setOpenChat(await getCharacterChat(ch.id))}>看全文</button>
        </li>)}</ul>
        {openChat && (
          <div style={{ marginTop: 8, borderTop: "1px solid #eee", paddingTop: 8 }}>
            <b>對話全文</b>
            {openChat.transcript.map((l, i) => (
              <div key={i} className="bubble them"><b>{l.speaker}：</b>{l.text}</div>
            ))}
            <p className="muted">📝 {openChat.summary}</p>
            <button className="ghost" onClick={() => setOpenChat(null)}>關閉</button>
          </div>
        )}
      </div>

      {err && <p className="err">{err}</p>}
    </main>
  );
}
