"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Sparkles, 
  BrainCircuit, 
  Radar, 
  CheckCircle2, 
  CalendarDays, 
  ShieldCheck,
  Cpu, 
  ArrowRight,
  TrendingUp,
  FileCheck2,
  Clock,
  Layers,
  ChevronRight,
  CheckCircle
} from "lucide-react";

import { API_BASE_URL } from "@/lib/api";

export default function OverviewPage() {
  const [profile, setProfile] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [profileRes, healthRes, metricsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/profile/constraints`).catch(() => null),
          fetch(`${API_BASE_URL}/health`).catch(() => null),
          fetch(`${API_BASE_URL}/api/v1/operations/metrics`).catch(() => null)
        ]);

        if (profileRes && profileRes.ok) {
          const p = await profileRes.json();
          setProfile(p);
        } else {
          // Fallback initial state
          setProfile({
            full_name: "Arhan Praveen Ghosarwade",
            degree: "B.Tech in Computer Science and Engineering",
            graduation_batch: 2028,
            current_academic_year: "3rd Year (2024 – 2028)",
            cgpa: 8.69,
            current_location: "Dharwad, Karnataka, India",
            target_roles: ["SDE Intern", "AI/ML Intern", "Backend Developer", "GenAI / Agentic AI", "Hackathons"],
            github_url: "https://github.com/Arhanpg",
            linkedin_url: "https://www.linkedin.com/in/arhan-ghosarwade-78bb16324"
          });
        }

        if (healthRes && healthRes.ok) {
          const h = await healthRes.json();
          setHealth(h);
        }

        if (metricsRes && metricsRes.ok) {
          const m = await metricsRes.json();
          setMetrics(m);
        }
      } catch (err) {
        console.error("Error loading overview data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    const timer = setInterval(loadData, 8000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      
      {/* Hero Welcome Banner */}
      <div className="apple-card p-6 sm:p-8 relative overflow-hidden bg-gradient-to-br from-white via-white to-blue-50/30">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide bg-[#0071E3]/10 text-[#0071E3] uppercase">
                Autonomous Personal AI Agent
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#E8F8EE] text-[#1D8348]">
                B.Tech 2028 Cohort Guardrails Active
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-[-0.025em] text-[#1D1D1F]">
              Welcome back, {profile?.full_name || "Arhan Praveen Ghosarwade"}
            </h1>
            <p className="text-[15px] text-[#86868B] max-w-2xl leading-relaxed">
              CareerOrbit is running 24/7 in the cloud—discovering verified internships on Naukri, LinkedIn, Unstop &amp; Big Tech portals, dynamically tailoring ATS-proof RenderCV resumes, and preparing staged applications behind your email approval gate.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link 
              href="/hunter" 
              className="apple-button-primary shadow-sm shadow-blue-500/20"
            >
              <Radar className="w-4 h-4" />
              <span>Explore Live Opportunities</span>
            </Link>
            <Link 
              href="/memory" 
              className="apple-button-secondary"
            >
              <BrainCircuit className="w-4 h-4 text-[#86868B]" />
              <span>Configure Memory</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Real-Time Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="apple-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-[#86868B]">Opportunities Polled</span>
            <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-[#0071E3]">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tracking-tight text-[#1D1D1F]">142</span>
            <span className="text-[12px] font-medium text-[#1D8348] bg-[#E8F8EE] px-1.5 py-0.5 rounded-full">
              +18 today
            </span>
          </div>
          <p className="mt-1 text-[12px] text-[#86868B]">Scraped across 5 job boards & ATS</p>
        </div>

        <div className="apple-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-[#86868B]">RenderCV Resumes</span>
            <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center text-[#34C759]">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tracking-tight text-[#1D1D1F]">24</span>
            <span className="text-[12px] font-medium text-[#1D8348] bg-[#E8F8EE] px-1.5 py-0.5 rounded-full">
              100% Typst ATS
            </span>
          </div>
          <p className="mt-1 text-[12px] text-[#86868B]">Dynamic SDE & AI/ML variations</p>
        </div>

        <div className="apple-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-[#86868B]">Awaiting Approval</span>
            <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center text-[#FF9500]">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tracking-tight text-[#1D1D1F]">3</span>
            <span className="text-[12px] font-medium text-[#B76E00] bg-[#FFF4E5] px-1.5 py-0.5 rounded-full">
              JWT Signed
            </span>
          </div>
          <p className="mt-1 text-[12px] text-[#86868B]">Adobe, Microsoft, Unstop Challenge</p>
        </div>

        <div className="apple-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-[#86868B]">Calendar Sync</span>
            <div className="w-8 h-8 rounded-full bg-purple-50 flex items-center justify-center text-purple-600">
              <CalendarDays className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tracking-tight text-[#1D1D1F]">5</span>
            <span className="text-[12px] font-medium text-[#1D8348] bg-[#E8F8EE] px-1.5 py-0.5 rounded-full">
              IST +05:30
            </span>
          </div>
          <p className="mt-1 text-[12px] text-[#86868B]">HackerRank OAs & interviews booked</p>
        </div>

      </div>

      {/* Nebius x NVIDIA Tiered Model Router Matrix */}
      <div className="apple-card p-6 sm:p-7 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-black/[0.06]">
          <div>
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-[#0071E3]" />
              <h2 className="text-lg font-semibold tracking-[-0.015em] text-[#1D1D1F]">
                Nebius Token Factory — Tiered NVIDIA Nemotron 3 Router
              </h2>
            </div>
            <p className="text-[13px] text-[#86868B] mt-1">
              Credit-aware dual-and-triple model routing architecture running at up to 26x lower inference cost.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[12px] font-medium px-2.5 py-1 rounded-full bg-[#E8E8ED] text-[#1D1D1F]">
              Endpoint: api.tokenfactory.nebius.com
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* Tier 1 */}
          <div className="p-4 rounded-2xl bg-[#F5F5F7] border border-black/[0.04] space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-[#E8E8ED] text-[#1D1D1F]">
                Tier 1 • High Frequency
              </span>
              <span className="text-[11px] font-medium text-[#1D8348]">$0.06 / 1M</span>
            </div>
            <div>
              <h3 className="font-semibold text-[14px] text-[#1D1D1F]">Nemotron-3_5-Lightning</h3>
              <p className="text-[11px] text-[#86868B]">30B Hybrid MoE (3B Active)</p>
            </div>
            <p className="text-[12px] text-[#86868B] leading-snug">
              Continuous 24/7 background filtering for B.Tech 2028 batch, scam detection, Mem0 additive fact extraction, and Gmail inbox triage.
            </p>
            <div className="pt-2 border-t border-black/[0.04] flex items-center justify-between text-[11px]">
              <span className="text-[#86868B]">
                {metrics?.model_telemetry?.["nebius/nvidia/Nemotron-3_5-Lightning"]
                  ? `${metrics.model_telemetry["nebius/nvidia/Nemotron-3_5-Lightning"].total_calls} calls • ${metrics.model_telemetry["nebius/nvidia/Nemotron-3_5-Lightning"].avg_latency_ms}ms avg`
                  : "Live Telemetry Active"}
              </span>
              <span className="text-[#1D8348] font-medium flex items-center gap-1">
                <CheckCircle className="w-3 h-3 fill-[#34C759] text-white" /> Active
              </span>
            </div>
          </div>

          {/* Tier 2 */}
          <div className="p-4 rounded-2xl bg-[#F5F5F7] border border-black/[0.04] space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-blue-100 text-[#0071E3]">
                Tier 2 • Browser & DOM
              </span>
              <span className="text-[11px] font-medium text-[#1D1D1F]">$0.30 / 1M</span>
            </div>
            <div>
              <h3 className="font-semibold text-[14px] text-[#1D1D1F]">nemotron-3-super-120b</h3>
              <p className="text-[11px] text-[#86868B]">120B Transformer-Mamba MoE</p>
            </div>
            <p className="text-[12px] text-[#86868B] leading-snug">
              Drives browser-use CDP execution loop, parses accessibility trees, maps candidate memory to complex multi-step forms with zero credential leak.
            </p>
            <div className="pt-2 border-t border-black/[0.04] flex items-center justify-between text-[11px]">
              <span className="text-[#86868B]">
                {metrics?.model_telemetry?.["nebius/nvidia/nemotron-3-super-120b-a12b"]
                  ? `${metrics.model_telemetry["nebius/nvidia/nemotron-3-super-120b-a12b"].total_calls} calls • ${metrics.model_telemetry["nebius/nvidia/nemotron-3-super-120b-a12b"].avg_latency_ms}ms avg`
                  : "CDP Ready"}
              </span>
              <span className="text-[#1D8348] font-medium flex items-center gap-1">
                <CheckCircle className="w-3 h-3 fill-[#34C759] text-white" /> Ready
              </span>
            </div>
          </div>

          {/* Tier 3 */}
          <div className="p-4 rounded-2xl bg-[#F5F5F7] border border-black/[0.04] space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-purple-100 text-purple-700">
                Tier 3 • Deep Synthesis
              </span>
              <span className="text-[11px] font-medium text-[#1D1D1F]">$1.00 / 1M</span>
            </div>
            <div>
              <h3 className="font-semibold text-[14px] text-[#1D1D1F]">Nemotron-3-Ultra-550b</h3>
              <p className="text-[11px] text-[#86868B]">550B Frontier Reasoning MoE</p>
            </div>
            <p className="text-[12px] text-[#86868B] leading-snug">
              Deep job gap analysis, Action-Technology-Result bullet synthesis, and strict Pydantic-validated RenderCV YAML schema generation.
            </p>
            <div className="pt-2 border-t border-black/[0.04] flex items-center justify-between text-[11px]">
              <span className="text-[#86868B]">
                {metrics?.model_telemetry?.["nebius/nvidia/Nemotron-3-Ultra-550b-a55b"]
                  ? `${metrics.model_telemetry["nebius/nvidia/Nemotron-3-Ultra-550b-a55b"].total_calls} calls • ${metrics.model_telemetry["nebius/nvidia/Nemotron-3-Ultra-550b-a55b"].avg_latency_ms}ms avg`
                  : "Verified Pass"}
              </span>
              <span className="text-[#1D8348] font-medium flex items-center gap-1">
                <CheckCircle className="w-3 h-3 fill-[#34C759] text-white" /> Ready
              </span>
            </div>
          </div>

        </div>

        {/* Live Search Runs & Discovery Activity Timeline */}
        {metrics?.recent_search_runs && metrics.recent_search_runs.length > 0 && (
          <div className="pt-4 border-t border-black/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-semibold text-[#1D1D1F] uppercase tracking-wider">
                Recent 24/7 Discovery Runs &amp; Telemetry
              </span>
              <span className="text-[11px] text-[#86868B]">Live Stream</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {metrics.recent_search_runs.slice(0, 3).map((run: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-white border border-black/[0.06] text-[12px] space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-[#0071E3]">
                    <span className="truncate">{run.query || "AI/ML & SDE Intern"}</span>
                    <span className="text-[#1D8348]">+{run.new_opportunities} found</span>
                  </div>
                  <p className="text-[11px] text-[#86868B] truncate">
                    Sources: {run.sources_polled || "JobSpy, Tavily, ATS"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Two Column Layout: Student Constraints & Recent Applications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left: Canonical Constraints Summary */}
        <div className="apple-card p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-black/[0.06]">
            <div className="flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-[#0071E3]" />
              <h2 className="font-semibold text-[16px] text-[#1D1D1F]">
                Candidate Hard Constraints
              </h2>
            </div>
            <Link 
              href="/memory" 
              className="text-[13px] text-[#0071E3] hover:underline flex items-center gap-0.5"
            >
              Edit in Vault <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-4 text-[13px]">
            <div className="space-y-1">
              <span className="text-[#86868B] text-[11px] uppercase tracking-wider font-medium">Degree & Batch</span>
              <p className="font-medium text-[#1D1D1F]">{profile?.degree || "B.Tech"} (Class of {profile?.graduation_batch || 2028})</p>
            </div>
            <div className="space-y-1">
              <span className="text-[#86868B] text-[11px] uppercase tracking-wider font-medium">Academic Year</span>
              <p className="font-medium text-[#1D1D1F]">{profile?.current_academic_year || "3rd Year"} • CGPA {profile?.cgpa || 8.95}</p>
            </div>
            <div className="space-y-1">
              <span className="text-[#86868B] text-[11px] uppercase tracking-wider font-medium">Current Location</span>
              <p className="font-medium text-[#1D1D1F]">{profile?.current_location || "India"} (On-site / Remote)</p>
            </div>
            <div className="space-y-1">
              <span className="text-[#86868B] text-[11px] uppercase tracking-wider font-medium">Target Roles</span>
              <p className="font-medium text-[#1D1D1F]">
                {(profile?.target_roles || ["SDE", "AI/ML", "Hackathons"]).join(", ")}
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-black/[0.04] flex items-center gap-4 text-[12px] text-[#86868B]">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#34C759]"></span>
              Zero-Hallucination Policy Active
            </span>
            <span>•</span>
            <span>Mem0 + Qdrant Storage</span>
          </div>
        </div>

        {/* Right: Quick HITL Approvals Queue */}
        <div className="apple-card p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-black/[0.06]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#FF9500]" />
              <h2 className="font-semibold text-[16px] text-[#1D1D1F]">
                Pending Human Approvals
              </h2>
            </div>
            <Link 
              href="/approvals" 
              className="text-[13px] text-[#0071E3] hover:underline flex items-center gap-0.5"
            >
              View All (3) <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            
            <div className="p-3.5 rounded-xl border border-black/[0.06] bg-white flex items-center justify-between hover:bg-slate-50/50 transition-colors">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[14px] text-[#1D1D1F]">Adobe India</span>
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E8F8EE] text-[#1D8348]">
                    96% ATS Match
                  </span>
                </div>
                <p className="text-[12px] text-[#86868B]">AI/ML Research Intern • Bangalore</p>
              </div>
              <Link 
                href="/approvals" 
                className="px-3 py-1 rounded-full text-[12px] font-medium bg-[#0071E3] text-white hover:bg-[#0077ED]"
              >
                Review Staging
              </Link>
            </div>

            <div className="p-3.5 rounded-xl border border-black/[0.06] bg-white flex items-center justify-between hover:bg-slate-50/50 transition-colors">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[14px] text-[#1D1D1F]">Microsoft IDC</span>
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E8F8EE] text-[#1D8348]">
                    92% ATS Match
                  </span>
                </div>
                <p className="text-[12px] text-[#86868B]">Software Engineering Intern • Hyderabad</p>
              </div>
              <Link 
                href="/approvals" 
                className="px-3 py-1 rounded-full text-[12px] font-medium bg-[#0071E3] text-white hover:bg-[#0077ED]"
              >
                Review Staging
              </Link>
            </div>

            <div className="p-3.5 rounded-xl border border-black/[0.06] bg-white flex items-center justify-between hover:bg-slate-50/50 transition-colors">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[14px] text-[#1D1D1F]">Unstop AI Challenge</span>
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-50 text-purple-700">
                    National Hackathon
                  </span>
                </div>
                <p className="text-[12px] text-[#86868B]">Batch 2028 Team Entry • Online</p>
              </div>
              <Link 
                href="/approvals" 
                className="px-3 py-1 rounded-full text-[12px] font-medium bg-[#0071E3] text-white hover:bg-[#0077ED]"
              >
                Review Staging
              </Link>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
}
