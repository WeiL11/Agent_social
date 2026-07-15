"use client";

import { useEffect, useState } from "react";
import { avatarUrl, createMission, extractFromText, listCharacters, listMissions } from "../lib/api";
import type { Character, Mission } from "../lib/types";

const PLACEHOLDER = `把你和 ChatGPT / Claude / Gemini 的一段對話貼進來（越多越準，會先去識別化）。
系統會分析你的溝通風格，長出屬於你的小精靈。`;

export default function Home() {
  const [chars, setChars] = useState<Character[] | null>(null);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [text, setText] = useState("");
  const [goal, setGoal] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function load() {
    try {
      setChars(await listCharacters());
      setMissions(await listMissions());
    } catch { /* first paint before auth settles */ }
  }
  useEffect(() => {
    load();
    const t = setTimeout(load, 1500); // retry after silent guest sign-in
    window.addEventListener("auth-changed", load);
    return () => { clearTimeout(t); window.removeEventListener("auth-changed", load); };
  }, []);

  async function onCreateCharacter() {
    setBusy(true); setMsg("");
    try {
      const r = await extractFromText(text);
      setMsg(`✨ 生成了 ${r.created.length} 隻小精靈！`);
      setShowAdd(false); setText("");
      load();
    } catch (e: any) { setMsg(e.message); }
    setBusy(false);
  }

  async function onCreateMission() {
    setBusy(true); setMsg("");
    try {
      const m = await createMission(goal.trim());
      setGoal("");
      setMsg(m.items.length ? `🎉 找到 ${m.items.length} 個可能的同好！去「任務回報」看看` : "已出發尋找，去「任務回報」看結果");
      load();
    } catch (e: any) { setMsg(e.message); }
    setBusy(false);
  }

  const empty = chars !== null && chars.length === 0;

  return (
    <main className="container">
      {/* 首次體驗 */}
      {empty && (
        <div className="card" style={{ background: "linear-gradient(135deg,#efeaff,#fff)" }}>
          <h1>歡迎 👋</h1>
          <p>① 貼上一段你和 AI 的對話，長出「像你」的小精靈<br />
             ② 告訴牠你想找什麼（跑友？同好？有同樣經驗的人？）<br />
             ③ 牠會去找，回報給你，你決定要不要認識對方</p>
          <button onClick={() => setShowAdd(true)}>＋ 生成我的第一隻小精靈</button>
        </div>
      )}

      {/* ★ 主 CTA：交任務給小精靈 */}
      {!empty && chars !== null && (
        <div className="card" style={{ background: "linear-gradient(135deg,#efeaff,#fff)" }}>
          <h2 style={{ marginTop: 0 }}>告訴小精靈你想找什麼 🔎</h2>
          <textarea rows={2} value={goal} onChange={(e) => setGoal(e.target.value)}
            placeholder="例如：我最近開始跑步，想找一起晨跑的人／我在用 Claude 做 UI，想找有類似經驗的人" />
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={onCreateMission} disabled={busy || goal.trim().length < 4}>
              {busy ? "小精靈出發中…" : "🚀 出發尋找"}
            </button>
            {missions.length > 0 && <a href="/missions">進行中任務（{missions.length}）→</a>}
          </div>
        </div>
      )}
      {msg && <p className="muted">{msg}</p>}

      {/* 我的小精靈 */}
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>我的小精靈 {chars ? `(${chars.length})` : ""}</h2>
        {!empty && <button className="ghost" onClick={() => setShowAdd(!showAdd)}>＋ 新增</button>}
      </div>

      {showAdd && (
        <div className="card">
          <h3>用你的 AI 對話生成</h3>
          <p className="muted">內容會先去除個資，只保留性格分析結果，不儲存原文。</p>
          <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder={PLACEHOLDER} />
          {text.trim().length > 0 && text.trim().length < 20 && (
            <p className="err" style={{ margin: "6px 0 0" }}>
              再多貼一點（至少 20 字，目前 {text.trim().length} 字）——越長分析越準
            </p>
          )}
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={onCreateCharacter} disabled={busy || text.trim().length < 20}
              title={text.trim().length < 20 ? "至少貼 20 字的對話內容" : ""}>
              {busy ? "分析中…" : text.trim().length < 20 ? `分析並生成（還差 ${20 - text.trim().length} 字）` : "分析並生成"}
            </button>
            <button className="ghost" onClick={() => setShowAdd(false)}>取消</button>
          </div>
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
