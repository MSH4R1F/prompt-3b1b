import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "3b1b Video Maker",
  description: "Generate narrated 3b1b-style explainer videos",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
