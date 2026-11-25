import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AskLens - AI Data Analyst Platform",
  description: "Senior AI Data Analyst & Scientist Platform with Safe SQL & Voice",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full overflow-hidden antialiased">{children}</body>
    </html>
  );
}
