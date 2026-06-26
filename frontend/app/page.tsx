"use client";

import { useEffect, useState } from "react";
import { avatarUrl, generateFromProfile, listCharacters } from "../lib/api";
import { SAMPLE_PROFILE } from "../lib/sample";
import type { Character } from "../lib/types";

export default function Home() {
  const [chars, setChars] = useState<Character[] | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [json, setJson] = useState(JSON.stringify(SAMPLE_PROFILE, null, 2));
  const [err, setErr] = useState("");

  async function load() {
    try { setChars(await listCharacters()); } catch (e: any) { setErr(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function onCreate() {
    setErr("");
    try {
      await generateFromProfile(JSON.parse(json));
      setShowAdd(false);
      load();
    } catch (e: any) { setErr(e.message); }
  }

  const empty = chars !== null && chars.length === 0;

  return (
    <main className="container">
      {/* First-open intro */}
      {empty && (
        <div className="card" style={{ background: "linear-gradient(135deg,#efeaff,#fff)" }}>
          <h1>歡迎 👋</h1>
          <p>把你跟 AI 的對話「性格」變成一隻小精靈。養成牠、派牠冒險，再用牠幫你配對到合得來的人。</p>
          <ol className="muted">
            <li>① 貼上你的「自我萃取側寫」JSON（或先用範例）</li>
            <li>② 生成你的第一隻角色</li>
            <li>③ 到「朋友 / 配對」找同類</li>
          </ol>
          <button onClick={() => setShowAdd(true)}>＋ 生成我的第一隻角色</button>
        </div>
      )}

      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>我的角色 {chars ? `(${chars.length})` : ""}</h2>
        {!empty && <button onClick={() => setShowAdd(!showAdd)}>＋ 新增角色</button>}
      </div>

      {/* Add-character window */}
      {showAdd && (
        <div className="card">
          <h3>新增角色</h3>
          <p className="muted">貼上自我萃取側寫 JSON（在你自己的 AI 跑出來的），或直接用預填範例。</p>
          <textarea rows={10} value={json} onChange={(e) => setJson(e.target.value)}
            style={{ fontFamily: "monospace", fontSize: 12 }} />
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={onCreate}>生成</button>
            <button className="ghost" onClick={() => setShowAdd(false)}>取消</button>
          </div>
          {err && <p className="err">{err}</p>}
        </div>
      )}

      {chars === null ? <p className="muted">載入中…</p> : (
        <div className="grid">
          {chars.map((c) => (
            <a key={c.id} href={`/character/${c.id}`} className="card" style={{ textAlign: "center" }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={avatarUrl(c.id)} width={88} height={88} alt={c.name ?? ""} />
              <div><b>{c.name}</b></div>
              <div className="muted">{c.archetype} · Lv{c.level}</div>
            </a>
          ))}
        </div>
      )}
    </main>
  );
}
