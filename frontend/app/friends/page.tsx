"use client";

import { useEffect, useState } from "react";
import {
  acceptFriend, avatarUrl, getMatches, listFriends, sendFriendRequest, wave,
} from "../../lib/api";
import type { Friend, Match } from "../../lib/types";

export default function FriendsPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [handle, setHandle] = useState("");
  const [msg, setMsg] = useState("");

  async function load() {
    try {
      setMatches(await getMatches());
      setFriends(await listFriends());
    } catch (e: any) { setMsg(e.message); }
  }
  useEffect(() => { load(); }, []);

  return (
    <main className="container">
      {/* Matchmaking */}
      <h2>推薦給你的人（配對）</h2>
      <p className="muted">分身幫你找性格合得來的人。互相揮手就會成為朋友。</p>
      {matches.length === 0 && <p className="muted">目前沒有推薦（要先有角色、且對方開啟「可被發現」）。</p>}
      {matches.map((m) => (
        <div key={m.their_character.id} className="card row">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={avatarUrl(m.their_character.id)} width={56} height={56} alt="" />
          <div style={{ flex: 1 }}>
            <b>{m.their_character.name}</b> <span className="pill">契合 {m.score}</span>
            <div className="muted">{m.reasons.join("、")}</div>
          </div>
          <button disabled={m.waved} onClick={async () => {
            const r = await wave(m.their_character.id);
            setMsg(r.matched ? "🎉 互相揮手，成為朋友了！" : "已送出揮手，等對方回應");
            load();
          }}>{m.waved ? "已揮手" : "👋 揮手"}</button>
        </div>
      ))}

      {/* Friend list */}
      <h2 style={{ marginTop: 24 }}>我的朋友</h2>
      <div className="row">
        <input value={handle} onChange={(e) => setHandle(e.target.value)} placeholder="用 handle 加朋友" />
        <button onClick={async () => {
          setMsg(""); try { await sendFriendRequest(handle); setHandle(""); load(); }
          catch (e: any) { setMsg(e.message); }
        }}>送出</button>
      </div>
      {msg && <p className="muted">{msg}</p>}
      <ul>
        {friends.map((f) => (
          <li key={f.friendship_id} style={{ margin: "6px 0" }}>
            @{f.handle} <span className="muted">[{f.direction}]</span>{" "}
            {f.direction === "incoming" &&
              <button className="ghost" onClick={async () => { await acceptFriend(f.friendship_id); load(); }}>接受</button>}
            {f.direction === "friends" && <a href={`/chat/${f.user_id}`}>聊天 →</a>}
          </li>
        ))}
      </ul>
    </main>
  );
}
