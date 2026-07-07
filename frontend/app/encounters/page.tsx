"use client";

import { useEffect, useState } from "react";
import { avatarUrl, explore, listCharacters, myEncounters, wave } from "../../lib/api";
import type { Character, Encounter } from "../../lib/types";

export default function EncountersPage() {
  const [chars, setChars] = useState<Character[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [open, setOpen] = useState<string | null>(null); // chat_id with expanded transcript
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setChars(await listCharacters());
      setEncounters(await myEncounters());
    } catch (e: any) { setMsg(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function goExplore(id: string) {
    setBusy(true); setMsg("");
    try {
      const r = await explore(id);
      setMsg(r.message + (r.encounter ? `（今天還能出門 ${r.remaining_today} 次）` : ""));
      load();
    } catch (e: any) { setMsg(e.message); }
    setBusy(false);
  }

  async function onWave(e: Encounter) {
    const r = await wave(e.other_character.id, e.my_character.id);
    setMsg(r.matched ? "🎉 對方也揮過手，你們成為朋友了！去「朋友/配對」開聊！" : "👋 已揮手，等對方回應。");
    load();
  }

  return (
    <main className="container">
      <h2>今日邂逅</h2>
      <p className="muted">讓小精靈出門，系統會找「最合得來的陌生小精靈」聊上幾句。看完摘要，喜歡就揮手——對方主人也揮手，你們就成為朋友。</p>

      <div className="card row" style={{ flexWrap: "wrap" }}>
        {chars.map((c) => (
          <button key={c.id} disabled={busy} onClick={() => goExplore(c.id)}>
            🚪 讓「{c.name}」出門
          </button>
        ))}
        {chars.length === 0 && <span className="muted">先到「我的角色」生成一隻小精靈。</span>}
      </div>
      {msg && <p className="muted">{msg}</p>}

      {encounters.map((e) => (
        <div key={e.chat_id} className="card">
          <div className="row">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={avatarUrl(e.my_character.id)} width={44} height={44} alt="" />
            <span className="muted">遇見</span>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={avatarUrl(e.other_character.id)} width={56} height={56} alt="" />
            <div style={{ flex: 1 }}>
              <b>{e.other_character.name}</b> <span className="pill">契合 {e.compatibility}</span>
              <div className="muted">{e.other_character.archetype} · Lv{e.other_character.level} · {e.reasons.join("、")}</div>
            </div>
            <button disabled={e.waved} onClick={() => onWave(e)}>{e.waved ? "已揮手" : "👋 揮手"}</button>
          </div>

          {/* 對方小精靈的資料 */}
          <div style={{ marginTop: 6 }}>
            {(e.other_character.trait_tags || []).map((t) => <span key={t} className="pill">{t}</span>)}
            <div className="muted">{e.other_character.persona}</div>
          </div>

          {/* 摘要 + 全文 */}
          <p style={{ marginBottom: 4 }}>📝 {e.summary}</p>
          <button className="ghost" onClick={() => setOpen(open === e.chat_id ? null : e.chat_id)}>
            {open === e.chat_id ? "收合對話" : "看對話全文"}
          </button>
          {open === e.chat_id && (
            <div style={{ marginTop: 8 }}>
              {e.transcript.map((l, i) => (
                <div key={i} className="bubble them"><b>{l.speaker}：</b>{l.text}</div>
              ))}
            </div>
          )}
        </div>
      ))}
      {encounters.length === 0 && <p className="muted">今天還沒有邂逅。讓小精靈出門吧！</p>}
    </main>
  );
}
