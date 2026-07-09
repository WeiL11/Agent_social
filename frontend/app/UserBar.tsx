"use client";

import { useEffect, useState } from "react";
import { chooseHandle, clearHandle, getHandle, getMe, setHandle } from "../lib/api";
import { authEnabled, getToken, signInWithGoogle, signOut } from "../lib/supabase";

function Overlay({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(30,20,60,.55)", zIndex: 100,
      display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="card" style={{ width: 360, textAlign: "center" }}>{children}</div>
    </div>
  );
}

/** Real auth (Supabase Google) with handle onboarding; dev-handle fallback locally. */
export default function UserBar() {
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
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
    const sync = () => {
      const t = Boolean(getToken());
      setSignedIn(t);
      setReady(true);
      if (t) refreshMe();
    };
    sync();
    window.addEventListener("auth-changed", sync);
    return () => window.removeEventListener("auth-changed", sync);
  }, []);

  if (!ready) return null;

  // ---- production: Supabase Google auth ----
  if (authEnabled) {
    if (!signedIn) {
      return (
        <Overlay>
          <h2>🪄 AI Persona</h2>
          <p className="muted">你的 AI 對話，會長成你的小精靈。</p>
          <button style={{ width: "100%" }} onClick={() => signInWithGoogle()}>
            使用 Google 登入
          </button>
        </Overlay>
      );
    }
    if (me?.placeholder) {
      return (
        <Overlay>
          <h2>取個名字 ✨</h2>
          <p className="muted">這是你在遊戲裡的公開暱稱（3–24 字，小寫英數、_ 或 -）</p>
          <input value={input} placeholder="例如 weilee" onChange={(e) => setInput(e.target.value)} />
          {err && <p className="err">{err}</p>}
          <button style={{ marginTop: 10, width: "100%" }} disabled={!input.trim()}
            onClick={async () => {
              setErr("");
              try { await chooseHandle(input.trim()); await refreshMe(); }
              catch (e: any) { setErr(e.message.includes("409") ? "這個暱稱已被使用" : e.message); }
            }}>確定</button>
        </Overlay>
      );
    }
    return (
      <span className="muted" style={{ cursor: "pointer" }} title="點擊登出"
        onClick={async () => { await signOut(); location.reload(); }}>
        @{me?.handle ?? "…"} ⎋
      </span>
    );
  }

  // ---- local dev fallback: pick-a-handle mode ----
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
