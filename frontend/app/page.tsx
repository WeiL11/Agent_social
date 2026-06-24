"use client";

// ─────────────────────────────────────────────────────────────────────────
// BLANK CANVAS — redesign this freely.
// This starter only proves the backend connection and shows how to call the
// typed client in lib/api.ts. Replace everything below the divider with your
// own design. See API.md for the full contract.
// ─────────────────────────────────────────────────────────────────────────

import { useEffect, useState } from "react";
import { avatarUrl, cardUrl, generateFromProfile, getHealth, listCharacters } from "../lib/api";
import { SAMPLE_PROFILE } from "../lib/sample";
import type { Character } from "../lib/types";

export default function Home() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [chars, setChars] = useState<Character[]>([]);
  const [err, setErr] = useState("");

  async function load() {
    try { setChars(await listCharacters()); } catch (e: any) { setErr(e.message); }
  }
  useEffect(() => {
    getHealth().then((h) => setOnline(h.db)).catch(() => setOnline(false));
    load();
  }, []);

  return (
    <main style={{ maxWidth: 640, margin: "48px auto", padding: "0 20px" }}>
      <h1>AI Persona Game — frontend canvas</h1>
      <p style={{ color: "#888" }}>
        後端連線：{online === null ? "…" : online ? "✅ online" : "❌ offline（後端有開嗎？）"}
      </p>
      <p style={{ color: "#aaa", fontSize: 13 }}>
        這是空白起點，示範如何呼叫 <code>lib/api.ts</code>。請從這裡開始重畫 UI；契約見 <code>API.md</code>。
      </p>

      <hr style={{ margin: "24px 0", border: 0, borderTop: "1px solid #eee" }} />

      <button onClick={async () => { try { await generateFromProfile(SAMPLE_PROFILE); load(); } catch (e: any) { setErr(e.message); } }}>
        用範例側寫生成角色
      </button>
      {err && <p style={{ color: "#c00" }}>{err}</p>}

      <h2 style={{ marginTop: 24 }}>我的角色（{chars.length}）</h2>
      <div style={{ display: "grid", gap: 12 }}>
        {chars.map((c) => (
          <div key={c.id} style={{ display: "flex", gap: 12, alignItems: "center", border: "1px solid #eee", borderRadius: 8, padding: 8, background: "#fff" }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={avatarUrl(c.id)} width={56} height={56} alt={c.name ?? "avatar"} />
            <div>
              <b>{c.name}</b> · {c.archetype} · Lv{c.level}
              <div style={{ fontSize: 12, color: "#999" }}>{c.persona}</div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
