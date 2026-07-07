"use client";

import { useEffect, useState } from "react";
import { clearHandle, getHandle, setHandle } from "../lib/api";

/** Friendly-beta login: pick a handle once, stored locally, sent as X-Dev-User. */
export default function UserBar() {
  const [handle, setH] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [ready, setReady] = useState(false);

  useEffect(() => { setH(getHandle()); setReady(true); }, []);
  if (!ready) return null;

  if (!handle) {
    return (
      <div style={{
        position: "fixed", inset: 0, background: "rgba(30,20,60,.55)", zIndex: 100,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <div className="card" style={{ width: 340, textAlign: "center" }}>
          <h2>🪄 AI Persona</h2>
          <p className="muted">取一個暱稱開始（好友測試版，之後會換正式登入）</p>
          <input value={input} placeholder="例如 weilee"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && input.trim() && (setHandle(input), location.reload())} />
          <button style={{ marginTop: 10, width: "100%" }} disabled={!input.trim()}
            onClick={() => { setHandle(input); location.reload(); }}>開始</button>
        </div>
      </div>
    );
  }
  return (
    <span className="muted" style={{ cursor: "pointer" }} title="點擊登出"
      onClick={() => { clearHandle(); location.reload(); }}>@{handle} ⎋</span>
  );
}
