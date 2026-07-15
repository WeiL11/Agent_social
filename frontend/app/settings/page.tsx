"use client";

import { useEffect, useState } from "react";
import { getMe, setDiscoverable } from "../../lib/api";
import { authEnabled, isGuest, linkGoogle, signOut } from "../../lib/supabase";
import type { Me } from "../../lib/types";

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [guest, setGuest] = useState<boolean | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    const load = () => {
      getMe().then(setMe).catch((e) => setErr(e.message));
      if (authEnabled) isGuest().then(setGuest);
    };
    load();
    window.addEventListener("auth-changed", load);
    return () => window.removeEventListener("auth-changed", load);
  }, []);

  if (!me) return <main className="container"><p className="muted">{err || "載入中…"}</p></main>;

  return (
    <main className="container">
      <h2>設定</h2>

      <div className="card">
        <b>帳號</b>
        <div className="muted">@{me.handle}{authEnabled && guest && "（訪客帳號）"}</div>
        {authEnabled && guest === true && (
          <div style={{ marginTop: 10 }}>
            <p className="muted">⚠️ 訪客帳號存在這台裝置上——換裝置或清瀏覽器會遺失。綁定 Google 即可永久保留、跨裝置登入。</p>
            <button onClick={() => linkGoogle()}>🔗 用 Google 保留我的帳號</button>
          </div>
        )}
        {authEnabled && guest === false && (
          <div style={{ marginTop: 10 }}>
            <span className="pill">已綁定 Google ✓</span>{" "}
            <button className="ghost" onClick={async () => { await signOut(); location.reload(); }}>登出</button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>
            <b>可被找到（discoverable）</b>
            <div className="muted">關閉後，別人的小精靈任務搜尋、閒逛與配對都不會看到你。</div>
          </div>
          <button className={me.discoverable ? "" : "ghost"} onClick={async () => {
            setMe(await setDiscoverable(!me.discoverable));
          }}>{me.discoverable ? "開啟中" : "已關閉"}</button>
        </div>
      </div>

      <div className="card">
        <b>更多</b>
        <div className="muted" style={{ marginTop: 6 }}>
          <a href="/friends">配對推薦</a> ·{" "}
          <a href="/missions">閒逛發現</a>
        </div>
      </div>
    </main>
  );
}
