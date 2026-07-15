"use client";

import { useEffect, useState } from "react";
import {
  archiveMission, avatarUrl, explore, listCharacters, listMissions,
  myEncounters, rerunMission, wave,
} from "../../lib/api";
import type { Character, Encounter, Mission, MissionResultItem } from "../../lib/types";

function ResultCard({ it, myCharId, onWave }: {
  it: MissionResultItem; myCharId: string; onWave: (charId: string, myCharId: string) => void;
}) {
  const c = it.character;
  if (!c) return null;
  return (
    <div className="row" style={{ borderTop: "1px solid #f0eefb", paddingTop: 8, marginTop: 8 }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={avatarUrl(c.id)} width={48} height={48} alt="" />
      <div style={{ flex: 1 }}>
        <b>{c.name}</b> <span className="pill">match {it.score}</span>
        {it.type === "mutual_goal" && <span className="pill" style={{ background: "#ffe9f0", color: "#c2185b" }}>對方也在找</span>}
        <div className="muted">{it.reasons.join("｜")}</div>
      </div>
      <button disabled={it.waved} onClick={() => onWave(c.id, myCharId)}>
        {it.waved ? "已揮手" : "👋 揮手"}
      </button>
    </div>
  );
}

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [chars, setChars] = useState<Character[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setMissions(await listMissions());
      setChars(await listCharacters());
      setEncounters(await myEncounters());
    } catch (e: any) { setMsg(e.message); }
  }
  useEffect(() => {
    load();
    window.addEventListener("auth-changed", load);
    return () => window.removeEventListener("auth-changed", load);
  }, []);

  async function onWave(theirCharId: string, myCharId: string) {
    const r = await wave(theirCharId, myCharId);
    setMsg(r.matched ? "🎉 互相揮手，成為朋友了！去「朋友」開聊" : "👋 已揮手，等對方回應");
    load();
  }

  return (
    <main className="container">
      <h2>任務回報</h2>
      {msg && <p className="muted">{msg}</p>}
      {missions.length === 0 && <p className="muted">還沒有任務——回首頁告訴小精靈你想找什麼吧！</p>}

      {missions.map((m) => (
        <div key={m.id} className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <b>「{m.query_text}」</b>
            <span className="muted">{m.tags.map((t) => `#${t}`).join(" ")}</span>
          </div>
          <p style={{ margin: "8px 0" }}>📣 {m.report ?? "尚未回報"}</p>
          {m.items.map((it) => (
            <ResultCard key={it.character_id} it={it} myCharId={m.character_id} onWave={onWave} />
          ))}
          <div className="row" style={{ marginTop: 10 }}>
            <button className="ghost" disabled={busy} onClick={async () => {
              setBusy(true); setMsg("");
              try { await rerunMission(m.id); setMsg("重新找過了！"); load(); }
              catch (e: any) { setMsg(e.message.includes("429") ? "今天跑過上限了，明天再試" : e.message); }
              setBusy(false);
            }}>🔄 再找一次（今天 {m.runs_today}/3）</button>
            <button className="ghost" onClick={async () => { await archiveMission(m.id); load(); }}>封存</button>
          </div>
        </div>
      ))}

      {/* 閒逛發現（原邂逅，降級併入） */}
      <h3 style={{ marginTop: 28 }}>閒逛發現 🚪</h3>
      <p className="muted">沒有特定目標？讓小精靈出門隨便逛逛，認識合得來的陌生小精靈（每天 2 次）。</p>
      <div className="row" style={{ flexWrap: "wrap" }}>
        {chars.map((c) => (
          <button key={c.id} className="ghost" disabled={busy} onClick={async () => {
            setBusy(true);
            try { const r = await explore(c.id); setMsg(r.message); load(); }
            catch (e: any) { setMsg(e.message); }
            setBusy(false);
          }}>讓「{c.name}」出門逛逛</button>
        ))}
      </div>
      {encounters.map((e) => (
        <div key={e.chat_id} className="card">
          <div className="row">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={avatarUrl(e.other_character.id)} width={48} height={48} alt="" />
            <div style={{ flex: 1 }}>
              <b>{e.other_character.name}</b> <span className="pill">契合 {e.compatibility}</span>
              <div className="muted">📝 {e.summary}</div>
            </div>
            <button disabled={e.waved} onClick={() => onWave(e.other_character.id, e.my_character.id)}>
              {e.waved ? "已揮手" : "👋 揮手"}
            </button>
          </div>
        </div>
      ))}
    </main>
  );
}
