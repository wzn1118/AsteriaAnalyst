import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Asteria Analyst",
  description: "A local-first, evidence-bound data-to-decision delivery workbench.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" data-scroll-behavior="smooth">
      <body>{children}</body>
    </html>
  );
}
