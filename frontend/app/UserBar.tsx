"use client";

import { useEffect, useState } from "react";
import { chooseHandle, clearHandle, getHandle, getMe, setHandle } from "../lib/api";
import { authEnabled, ensureSignedIn, getToken } from "../lib/supabase";

function Overlay({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(30,20,60,.55)", zIndex: 100,
      display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="card" style={{ width: 360, textAlign: "center" }}>{children}</div>
    </div>
  );
}

/** Guest-first: an anonymous session is created silently on first visit — the
 * only thing we ask is a display name. Linking to Google lives in Settings. */
export default function UserBar() {
  const [ready, setReady] = useState(false);
  const [me, setMe] = useState<{ handle: string; placeholder: boolean } | null>(null);
  const [input, setInput] = useState("");
  const [err, setErr] = useState("");

  async function refreshMe() {
    try {
      const m = await getMe();
      setMe({ handle: m.handle, placeholder: m.handle_is_placeholder });
    } catch { setMe(null); }
  }

  useEffect(() => {
    if (!authEnabled) { setReady(true); return; }
    ensureSignedIn(); // guest session, no wall
    const sync = () => { setReady(true); if (getToken()) refreshMe(); };
    sync();
    window.addEventListener("auth-changed", sync);
    return () => window.removeEventListener("auth-changed", sync);
  }, []);

  if (!ready) return null;

  // ---- production (Supabase): silent guest; only ask for a name once ----
  if (authEnabled) {
    if (me?.placeholder) {
      return (
        <Overlay>
          <h2>幫自己取個名字 ✨</h2>
          <p className="muted">別人會用這個名字認識你（3–24 字，小寫英數、_ 或 -）</p>
          <input value={input} placeholder="例如 weilee" onChange={(e) => setInput(e.target.value)} />
          {err && <p className="err">{err}</p>}
          <button style={{ marginTop: 10, width: "100%" }} disabled={!input.trim()}
            onClick={async () => {
              setErr("");
              try { await chooseHandle(input.trim()); await refreshMe(); }
              catch (e: any) { setErr(e.message.includes("409") ? "這個名字已被使用" : e.message); }
            }}>開始</button>
        </Overlay>
      );
    }
    return <a href="/settings" className="muted">@{me?.handle ?? "…"}</a>;
  }

  // ---- local dev fallback: X-Dev-User handle mode ----
  const h = getHandle();
  if (!h) {
    return (
      <Overlay>
        <h2>🪄 AI Persona（本機開發）</h2>
        <input value={input} placeholder="dev handle" onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && input.trim() && (setHandle(input), location.reload())} />
        <button style={{ marginTop: 10, width: "100%" }} disabled={!input.trim()}
          onClick={() => { setHandle(input); location.reload(); }}>開始</button>
      </Overlay>
    );
  }
  return (
    <span className="muted" style={{ cursor: "pointer" }} title="點擊登出"
      onClick={() => { clearHandle(); location.reload(); }}>@{h} ⎋</span>
  );
}
