"use client";

import { useEffect, useRef, useState } from "react";
import { getMessages, sendMessage } from "../../../lib/api";
import type { DirectMessage } from "../../../lib/types";

export default function ChatRoom({ params }: { params: { friendUserId: string } }) {
  const fid = params.friendUserId;
  const [msgs, setMsgs] = useState<DirectMessage[]>([]);
  const [text, setText] = useState("");
  const [err, setErr] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  async function load() {
    try { setMsgs(await getMessages(fid)); } catch (e: any) { setErr(e.message); }
  }
  useEffect(() => {
    load();
    const t = setInterval(load, 4000); // rough polling (later: Supabase Realtime)
    return () => clearInterval(t);
  }, [fid]);
  useEffect(() => { endRef.current?.scrollIntoView(); }, [msgs]);

  async function send() {
    if (!text.trim()) return;
    try { await sendMessage(fid, text.trim()); setText(""); load(); }
    catch (e: any) { setErr(e.message); }
  }

  return (
    <main className="container">
      <a href="/friends" className="muted">← 朋友</a>
      <h2>聊天室</h2>
      {err && <p className="err">{err}</p>}
      <div className="card" style={{ minHeight: 320, display: "flex", flexDirection: "column" }}>
        {msgs.map((m) => (
          <div key={m.id} className={`bubble ${m.from_me ? "me" : "them"}`}>{m.body}</div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="row">
        <input value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()} placeholder="輸入訊息…" />
        <button onClick={send}>送出</button>
      </div>
    </main>
  );
}
