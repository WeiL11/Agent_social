"use client";

import { useEffect, useState } from "react";
import { avatarUrl, extractFromText, listCharacters } from "../lib/api";
import type { Character } from "../lib/types";

const PLACEHOLDER = `把你和 ChatGPT / Claude / Gemini 的一段對話貼進來（越多越準，會先去識別化）。

例如直接複製你最近問 AI 的十幾則訊息。系統會分析你的溝通風格，長出屬於你的小精靈。`;

export default function Home() {
  const [chars, setChars] = useState<Character[] | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function load() {
    try { setChars(await listCharacters()); } catch { /* not logged in yet */ }
  }
  useEffect(() => { load(); }, []);

  async function onCreate() {
    setBusy(true); setMsg("");
    try {
      const r = await extractFromText(text);
      setMsg(`✨ 生成了 ${r.created.length} 隻小精靈！（分析引擎：${r.engine === "gemini" ? "Gemini" : "規則"}）`
        + (r.skipped_facets.length ? `｜已滿 ${r.slot_cap} 隻，略過：${r.skipped_facets.join("、")}` : ""));
      setShowAdd(false); setText("");
      load();
    } catch (e: any) { setMsg(e.message); }
    setBusy(false);
  }

  const empty = chars !== null && chars.length === 0;

  return (
    <main className="container">
      {empty && (
        <div className="card" style={{ background: "linear-gradient(135deg,#efeaff,#fff)" }}>
          <h1>歡迎 👋</h1>
          <p>貼上一段你和 AI 的對話，你的「性格」會長成一隻小精靈。<br />
            養成牠、讓牠每天出門認識別的小精靈，再決定要不要跟對方的主人交朋友。</p>
          <button onClick={() => setShowAdd(true)}>＋ 生成我的第一隻小精靈</button>
        </div>
      )}

      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>我的角色 {chars ? `(${chars.length})` : ""}</h2>
        {!empty && <button onClick={() => setShowAdd(!showAdd)}>＋ 新增角色</button>}
      </div>

      {showAdd && (
        <div className="card">
          <h3>用你的 AI 對話生成角色</h3>
          <p className="muted">貼上你與 AI 的對話文字（至少幾百字較準）。內容會先去除 email/電話等個資，只保留性格分析結果，不儲存原文。</p>
          <textarea rows={10} value={text} onChange={(e) => setText(e.target.value)}
            placeholder={PLACEHOLDER} />
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={onCreate} disabled={busy || text.trim().length < 20}>
              {busy ? "分析中…" : "分析並生成"}
            </button>
            <button className="ghost" onClick={() => setShowAdd(false)}>取消</button>
          </div>
        </div>
      )}
      {msg && <p className="muted">{msg}</p>}

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
