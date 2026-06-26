"use client";

import { useEffect, useState } from "react";
import { getMe, setDiscoverable } from "../../lib/api";
import type { Me } from "../../lib/types";

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => { getMe().then(setMe).catch((e) => setErr(e.message)); }, []);

  if (!me) return <main className="container"><p className="muted">{err || "載入中…"}</p></main>;

  return (
    <main className="container">
      <h2>設定</h2>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div><b>帳號</b><div className="muted">@{me.handle}</div></div>
        </div>
      </div>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>
            <b>可被配對（discoverable）</b>
            <div className="muted">關閉後，別人的「配對推薦」不會看到你的角色。</div>
          </div>
          <button className={me.discoverable ? "" : "ghost"} onClick={async () => {
            const next = !me.discoverable;
            setMe(await setDiscoverable(next));
          }}>{me.discoverable ? "開啟中" : "已關閉"}</button>
        </div>
      </div>
    </main>
  );
}
