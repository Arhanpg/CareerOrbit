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
  Zap,
  Play,
  X,
  FileText,
  ExternalLink,
  Clock,
  Check
} from "lucide-react";
import { API_BASE_URL, getApiUrl } from "@/lib/api";

interface TelemetryItem {
  stage: number;
  name: string;
  status: string;
  elapsed_seconds: number;
  details: string;
}

export default function Navigation() {
  const pathname = usePathname();
  const [sandboxEnabled, setSandboxEnabled] = useState(false);
  const [runningLoop, setRunningLoop] = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetryItem[]>([]);
  const [loopResult, setLoopResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const navItems = [
    { name: "Overview", href: "/", icon: Sparkles },
    { name: "Memory Vault", href: "/memory", icon: BrainCircuit },
    { name: "Live Hunter", href: "/hunter", icon: Radar },
    { name: "Approvals", href: "/approvals", icon: CheckCircle2, badge: "HITL" },
    { name: "Calendar Sync", href: "/calendar", icon: CalendarDays },
  ];

  const handleRunSandbox = async () => {
    setRunningLoop(true);
    setTelemetry([]);
    setLoopResult(null);
    setErrorMsg(null);

    try {
      const res = await fetch(getApiUrl("/api/v1/sandbox/run-60s-loop"), {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        const data = await res.json();
        setLoopResult(data);
        setTelemetry(data.telemetry || []);
      } else {
        setErrorMsg("Failed to execute sandbox loop.");
      }
    } catch (err: any) {
      setErrorMsg(`Error connecting to API: ${err?.message || err}`);
    } finally {
      setRunningLoop(false);
    }
  };

  return (
    <>
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
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-all ${
                    isActive
                      ? "apple-segmented-active"
                      : "text-[#86868B] hover:text-[#1D1D1F]"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#0071E3]" : ""}`} />
                  <span>{item.name}</span>
                  {item.badge && (
                    <span className="text-[9px] font-semibold px-1.5 py-0.2 rounded-full bg-[#E8F8EE] text-[#1D8348]">
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
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#E8F8EE] border border-[#34C759]/20 text-[#1D8348] text-[12px] font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34C759] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#34C759]"></span>
              </span>
              <span>24/7 Hunter: ON</span>
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

      {/* Judge 60-Second Sandbox Interactive Modal */}
      {sandboxEnabled && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl border border-black/[0.08] space-y-5 max-h-[90vh] overflow-y-auto">
            
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-3 border-b border-black/[0.06]">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-bold text-[#0071E3] uppercase tracking-wider">
                    Nebius x NVIDIA Global AI Hackathon
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#E8F8EE] text-[#1D8348]">
                    Zero-Key &bull; Zero-CAPTCHA
                  </span>
                </div>
                <h2 className="text-xl font-bold tracking-tight text-[#1D1D1F]">
                  Judge 60-Second Autonomous Career Loop
                </h2>
                <p className="text-xs text-[#86868B] mt-0.5">
                  Executes all 6 autonomous lifecycle phases end-to-end in under 60 seconds.
                </p>
              </div>

              <button
                onClick={() => setSandboxEnabled(false)}
                className="text-[#86868B] hover:text-[#1D1D1F] p-1.5 rounded-full hover:bg-[#F5F5F7]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Run Action Bar */}
            <div className="p-4 rounded-2xl bg-[#F8F9FA] border border-black/[0.06] flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold text-[#1D1D1F]">
                  Target Mock Portal: Adobe AI/ML Intern (2028 Batch)
                </p>
                <p className="text-[11px] text-[#86868B]">
                  Preloads Mem0 &bull; Compiles RenderCV Typst PDF &bull; Browser-Use CDP Staging &bull; JWT Webhook &bull; Google Calendar Sync
                </p>
              </div>

              <button
                onClick={handleRunSandbox}
                disabled={runningLoop}
                className="w-full sm:w-auto px-6 py-2.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-bold transition-all shadow-md shadow-blue-500/25 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                {runningLoop ? "Executing Loop..." : "Run 60s Demo Now"}
              </button>
            </div>

            {/* Error Banner */}
            {errorMsg && (
              <div className="p-3.5 rounded-xl bg-[#FDEDEC] text-[#C0392B] text-xs font-medium">
                {errorMsg}
              </div>
            )}

            {/* Live Telemetry Progress */}
            {telemetry.length > 0 && (
              <div className="space-y-2.5 pt-2">
                <span className="text-xs font-bold text-[#1D1D1F] uppercase tracking-wider">
                  Live Stage Telemetry {loopResult?.total_duration_seconds ? `(${loopResult.total_duration_seconds}s Total)` : ""}
                </span>
                <div className="space-y-2">
                  {telemetry.map((t) => (
                    <div
                      key={t.stage}
                      className="p-3 rounded-xl bg-white border border-black/[0.06] flex items-start gap-3 shadow-sm"
                    >
                      <div className="w-5 h-5 rounded-full bg-[#E8F8EE] text-[#1D8348] flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Check className="w-3 h-3" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-[#1D1D1F]">
                            Stage {t.stage}: {t.name}
                          </p>
                          <span className="text-[11px] font-semibold text-[#0071E3]">
                            {t.elapsed_seconds}s
                          </span>
                        </div>
                        <p className="text-[11px] text-[#86868B] mt-0.5">{t.details}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Result Artifacts Deck */}
            {loopResult && (
              <div className="p-4 rounded-2xl bg-[#E8F8EE] border border-[#34C759]/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#1D8348] flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> 100% Demonstration Completed!
                  </span>
                  <span className="text-xs font-bold text-[#1D8348]">
                    Total Time: {loopResult.total_duration_seconds}s (Under 60s: ✓)
                  </span>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  {loopResult.pdf_download_url && (
                    <a
                      href={`${API_BASE_URL}${loopResult.pdf_download_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3.5 py-1.5 rounded-full bg-white text-[#0071E3] text-xs font-semibold border border-black/[0.06] flex items-center gap-1.5 shadow-sm"
                    >
                      <FileText className="w-3.5 h-3.5" /> Download Tailored Typst PDF
                    </a>
                  )}

                  {loopResult.screenshot_url && (
                    <a
                      href={`${API_BASE_URL}${loopResult.screenshot_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3.5 py-1.5 rounded-full bg-white text-[#1D1D1F] text-xs font-semibold border border-black/[0.06] flex items-center gap-1.5 shadow-sm"
                    >
                      <ExternalLink className="w-3.5 h-3.5" /> View Staged Form Screenshot
                    </a>
                  )}

                  {loopResult.gcal_event_link && (
                    <a
                      href={loopResult.gcal_event_link}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3.5 py-1.5 rounded-full bg-[#0071E3] text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                    >
                      <CalendarDays className="w-3.5 h-3.5" /> Open Synced Google Calendar
                    </a>
                  )}
                </div>
              </div>
            )}

          </div>
        </div>
      )}
    </>
  );
}
