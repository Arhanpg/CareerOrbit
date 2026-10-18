"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Sparkles, 
  BrainCircuit, 
  Radar, 
  CheckCircle2, 
  CalendarDays, 
  ShieldCheck,
  Zap
} from "lucide-react";

interface NavigationProps {
  sandboxMode?: boolean;
  onToggleSandbox?: (enabled: boolean) => void;
}

export default function Navigation() {
  const pathname = usePathname();
  const [sandboxEnabled, setSandboxEnabled] = useState(false);

  const navItems = [
    { name: "Overview", href: "/", icon: Sparkles },
    { name: "Memory Vault", href: "/memory", icon: BrainCircuit },
    { name: "Live Hunter", href: "/hunter", icon: Radar },
    { name: "Approvals", href: "/approvals", icon: CheckCircle2, badge: "3" },
    { name: "Calendar Sync", href: "/calendar", icon: CalendarDays },
  ];

  return (
    <header className="sticky top-0 z-50 w-full apple-frosted">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#0071E3] to-[#409CFF] flex items-center justify-center text-white shadow-sm shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <Zap className="w-4 h-4 fill-white" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-[17px] tracking-[-0.022em] text-[#1D1D1F]">
                CareerClaw
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-[#E8E8ED] text-[#86868B]">
                B.Tech 2028
              </span>
            </div>
          </div>
        </Link>

        {/* Center: Segmented Navigation Pill */}
        <nav className="hidden md:flex apple-segmented-nav shadow-inner">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative px-4 py-1.5 rounded-full text-[13px] font-medium transition-all duration-200 flex items-center gap-1.5 ${
                  isActive
                    ? "bg-white text-[#1D1D1F] shadow-[0_2px_8px_rgba(0,0,0,0.08)]"
                    : "text-[#86868B] hover:text-[#1D1D1F]"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#0071E3]" : "text-[#86868B]"}`} />
                <span>{item.name}</span>
                {item.badge && (
                  <span className="ml-0.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-[#0071E3] text-white">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right: Live Daemon Status & Judge Sandbox Toggle */}
        <div className="flex items-center gap-3">
          {/* Live Daemon Status Indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#E8F8EE] border border-[#34C759]/20 text-[#1D8348] text-[12px] font-medium">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34C759] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#34C759]"></span>
            </span>
            <span>24/7 Hunter Active</span>
          </div>

          {/* Judge 60s Sandbox Toggle */}
          <div className="flex items-center gap-2 pl-2 border-l border-black/[0.08]">
            <button
              onClick={() => setSandboxEnabled(!sandboxEnabled)}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all flex items-center gap-1.5 border ${
                sandboxEnabled
                  ? "bg-[#0071E3] text-white border-[#0071E3] shadow-sm shadow-blue-500/20"
                  : "bg-white text-[#1D1D1F] border-black/[0.08] hover:bg-[#F5F5F7]"
              }`}
              title="Deterministic 60-Second Demo for Hackathon Judges"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Judge 60s Demo: {sandboxEnabled ? "ON" : "OFF"}</span>
            </button>
          </div>

        </div>

      </div>
    </header>
  );
}
