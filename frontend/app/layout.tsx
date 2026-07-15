import "./globals.css";
import UserBar from "./UserBar";

export const metadata = {
  title: "AI Persona Game",
  description: "你的 AI 對話，會長成你的角色。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-Hant">
      <body>
        <nav className="topbar">
          <a className="brand" href="/">🪄 AI Persona</a>
          <a href="/">我的小精靈</a>
          <a href="/missions">任務回報</a>
          <a href="/friends">朋友</a>
          <a href="/settings">設定</a>
          <UserBar />
        </nav>
        {children}
      </body>
    </html>
  );
}
