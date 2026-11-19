import type { Metadata, Viewport } from "next";
import "@xyflow/react/dist/style.css";
import "./globals.css";
import { TopBar } from "@/components/TopBar";

export const metadata: Metadata = {
  title: "ModelFlow",
  description: "Design new workflows or improve existing ones. Visual workflow studio with explainable, evidence-linked model choices.",
};

export const viewport: Viewport = {
  themeColor: "#10111a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg text-ink antialiased">
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-accent focus:px-3 focus:py-2 focus:text-[#171321]">
          Skip to content
        </a>
        <TopBar />
        <div id="main">{children}</div>
      </body>
    </html>
  );
}
