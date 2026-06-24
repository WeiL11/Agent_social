import "./globals.css";

export const metadata = {
  title: "AI Persona Game",
  description: "你的 AI 對話，會長成你的角色。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
