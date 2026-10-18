import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

export const metadata: Metadata = {
  title: "CareerClaw | Autonomous AI Career Agent (B.Tech 2028)",
  description: "Autonomous Student Opportunity Hunter, Dynamic ATS Resume Compiler, HITL Browser Applier, and Inbox-to-Calendar Sync powered by NVIDIA Nemotron on Nebius Token Factory.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-[#F5F5F7] text-[#1D1D1F] flex flex-col`}>
        <Navigation />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
          {children}
        </main>
        <footer className="w-full border-t border-black/[0.06] bg-white/50 py-6 text-center text-[13px] text-[#86868B]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p>
              CareerClaw — Engineered for the <strong>Nebius x NVIDIA Global AI Hackathon</strong>. Open Source (MIT License).
            </p>
            <div className="flex items-center gap-4 text-[12px]">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#34C759]"></span>
                NVIDIA Nemotron 3 Models
              </span>
              <span>•</span>
              <span>Nebius Token Factory</span>
              <span>•</span>
              <span>Tavily Search API</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
