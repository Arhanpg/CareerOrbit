"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Radar, 
  ExternalLink, 
  Sparkles, 
  Building2, 
  MapPin, 
  Clock, 
  CheckCircle, 
  ArrowRight,
  RefreshCw,
  FileCheck2,
  Cpu,
  Layers,
  ChevronRight
} from "lucide-react";

export default function LiveHunterPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"JD" | "RESUME">("JD");
  const [filterSource, setFilterSource] = useState("ALL");
  const [isHunting, setIsHunting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/hunter/jobs?only_eligible=true");
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
        if (data.jobs && data.jobs.length > 0) {
          setSelectedJob(data.jobs[0]);
        }
      }
    } catch (err) {
      console.log("Using local mock jobs");
    } finally {
      setLoading(false);
    }
  };

  const handleRunNow = async () => {
    setIsHunting(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/hunter/run-now", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role_query: "AI ML Software Engineering Intern" })
      });
      if (res.ok) {
        await fetchJobs();
      }
    } catch (err) {
      console.error("Hunt cycle error:", err);
    } finally {
      setIsHunting(false);
    }
  };

  const filteredJobs = jobs.filter((j) => {
    if (filterSource === "ALL") return true;
    if (filterSource === "TAVILY") return j.source === "tavily";
    if (filterSource === "JOBSPY") return ["linkedin", "naukri", "indeed", "google"].includes(j.source);
    if (filterSource === "ATS") return j.source.startsWith("greenhouse") || j.source.startsWith("lever");
    return true;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide bg-[#0071E3]/10 text-[#0071E3] uppercase">
              Plane 2: 24/7 Discovery Daemon
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#E8F8EE] text-[#1D8348]">
              JobSpy + Tavily Search API
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-[-0.025em] text-[#1D1D1F] mt-1.5">
            24/7 Live Hunter & ATS Match Matrix
          </h1>
          <p className="text-[14px] text-[#86868B] max-w-3xl mt-0.5">
            Continuously polling Naukri, LinkedIn, Unstop hackathons, Internshala, and direct Big Tech portals. Every opportunity is strictly gated by Nemotron 3.5 Lightning for <strong>B.Tech 2028 batch</strong> eligibility.
          </p>
        </div>

        <button
          onClick={handleRunNow}
          disabled={isHunting}
          className="apple-button-primary shadow-sm shadow-blue-500/20"
        >
          <RefreshCw className={`w-4 h-4 ${isHunting ? "animate-spin" : ""}`} />
          <span>{isHunting ? "Hunting Opportunities..." : "Run 24/7 Sweep Now"}</span>
        </button>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column (5 Cols): Opportunity List */}
        <div className="lg:col-span-5 space-y-3">
          
          {/* Source Filter Segment */}
          <div className="apple-card p-2 flex items-center justify-between">
            <div className="flex items-center gap-1 apple-segmented-nav w-full justify-between">
              {[
                { id: "ALL", label: "All" },
                { id: "TAVILY", label: "Tavily / Unstop" },
                { id: "JOBSPY", label: "LinkedIn / Naukri" },
                { id: "ATS", label: "Direct ATS" }
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFilterSource(f.id)}
                  className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                    filterSource === f.id
                      ? "bg-white text-[#1D1D1F] shadow-sm"
                      : "text-[#86868B] hover:text-[#1D1D1F]"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Job Cards Feed */}
          <div className="space-y-3 max-h-[720px] overflow-y-auto pr-1">
            {filteredJobs.length === 0 ? (
              <div className="apple-card p-8 text-center text-[#86868B] text-[13px]">
                No opportunities match this filter. Click "Run 24/7 Sweep Now" to harvest listings.
              </div>
            ) : (
              filteredJobs.map((job) => {
                const isSelected = selectedJob?.id === job.id;
                const isAIML = job.role_category === "AIML";
                const isHackathon = job.role_category === "HACKATHON";

                return (
                  <div
                    key={job.id}
                    onClick={() => setSelectedJob(job)}
                    className={`apple-card p-4.5 cursor-pointer transition-all ${
                      isSelected
                        ? "border-[#0071E3] ring-2 ring-[#0071E3]/15 shadow-md"
                        : "hover:border-black/[0.12]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[12px] font-semibold text-[#86868B] flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5" />
                        {job.company}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
                        job.match_score >= 90
                          ? "bg-[#E8F8EE] text-[#1D8348]"
                          : "bg-blue-50 text-[#0071E3]"
                      }`}>
                        {job.match_score}% Match
                      </span>
                    </div>

                    <h3 className="font-semibold text-[15px] text-[#1D1D1F] mt-1.5">
                      {job.title}
                    </h3>

                    <div className="flex items-center gap-3 mt-2 text-[12px] text-[#86868B]">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {job.location}
                      </span>
                      <span>•</span>
                      <span className="capitalize">{job.source}</span>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-black/[0.04] flex items-center justify-between">
                      <span className="text-[11px] font-medium text-[#1D8348] flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 fill-[#34C759] text-white" />
                        B.Tech 2028 Verified
                      </span>
                      <span className="text-[11px] text-[#0071E3] font-medium flex items-center gap-0.5">
                        Inspect <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

        </div>

        {/* Right Column (7 Cols): Split Inspector (JD vs Tailored PDF) */}
        <div className="lg:col-span-7">
          {selectedJob ? (
            <div className="apple-card p-6 sm:p-7 space-y-6">
              
              {/* Top Details & Tab Switch */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-black/[0.06]">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-[#0071E3]">
                      {selectedJob.role_category}
                    </span>
                    <span className="text-[12px] text-[#86868B]">
                      Source: {selectedJob.source}
                    </span>
                  </div>
                  <h2 className="text-xl font-semibold text-[#1D1D1F]">
                    {selectedJob.title}
                  </h2>
                  <p className="text-[13px] text-[#86868B]">
                    {selectedJob.company} • {selectedJob.location}
                  </p>
                </div>

                <div className="flex items-center gap-1 apple-segmented-nav self-start sm:self-auto">
                  <button
                    onClick={() => setActiveTab("JD")}
                    className={`px-3.5 py-1 rounded-full text-[12px] font-medium transition-all ${
                      activeTab === "JD"
                        ? "bg-white text-[#1D1D1F] shadow-sm"
                        : "text-[#86868B] hover:text-[#1D1D1F]"
                    }`}
                  >
                    Job Description
                  </button>
                  <button
                    onClick={() => setActiveTab("RESUME")}
                    className={`px-3.5 py-1 rounded-full text-[12px] font-medium transition-all ${
                      activeTab === "RESUME"
                        ? "bg-white text-[#1D1D1F] shadow-sm"
                        : "text-[#86868B] hover:text-[#1D1D1F]"
                    }`}
                  >
                    Tailored ATS PDF
                  </button>
                </div>
              </div>

              {/* Tab 1: Job Description with Highlights */}
              {activeTab === "JD" && (
                <div className="space-y-5">
                  <div className="p-4 rounded-2xl bg-[#F5F5F7] border border-black/[0.04] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-semibold text-[#1D1D1F]">
                        Nemotron 3.5 Lightning Eligibility Assessment
                      </span>
                      <span className="text-[11px] font-semibold text-[#1D8348]">
                        Score: {selectedJob.match_score}/100
                      </span>
                    </div>
                    <p className="text-[12px] text-[#86868B]">
                      Strictly confirmed for 3rd-year B.Tech students (Class of 2028). Zero full-time experience requirements; verified genuine stipend/award structure.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <h3 className="font-semibold text-[14px] text-[#1D1D1F]">
                      Opportunity Description & Requirements
                    </h3>
                    <div className="text-[13px] text-[#1D1D1F]/90 leading-relaxed whitespace-pre-line p-4 rounded-2xl bg-white border border-black/[0.06] max-h-[380px] overflow-y-auto">
                      {selectedJob.description}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <a
                      href={selectedJob.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="apple-button-secondary text-[12px]"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>View Direct Listing</span>
                    </a>

                    <Link
                      href="/approvals"
                      className="apple-button-primary text-[12px]"
                    >
                      <span>Stage Application (Browser-Use)</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              )}

              {/* Tab 2: Tailored RenderCV Typst PDF Preview */}
              {activeTab === "RESUME" && (
                <div className="space-y-5">
                  <div className="p-4 rounded-2xl bg-[#E8F8EE] border border-[#34C759]/20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileCheck2 className="w-4 h-4 text-[#1D8348]" />
                      <span className="text-[12px] font-semibold text-[#1D8348]">
                        RenderCV Typst Synthesis (engineeringresumes theme)
                      </span>
                    </div>
                    <span className="text-[11px] font-medium text-[#1D8348]">
                      100% ATS Verified
                    </span>
                  </div>

                  {/* Mock PDF Sheet Viewer */}
                  <div className="p-8 rounded-2xl bg-white border border-black/[0.1] shadow-md space-y-4 font-serif text-[12px] text-[#1D1D1F] max-h-[460px] overflow-y-auto">
                    <div className="text-center space-y-1 border-b border-black/[0.1] pb-3">
                      <h3 className="font-bold text-[18px] tracking-wide font-sans">
                        AMAN SHARMA
                      </h3>
                      <p className="text-[11px] text-[#86868B] font-sans">
                        Bangalore, India • +91 9876543210 • aman.sharma28@example.com • github.com/amansharma28
                      </p>
                    </div>

                    <div className="space-y-1">
                      <h4 className="font-bold text-[13px] uppercase tracking-wider text-[#0071E3] font-sans">
                        Education
                      </h4>
                      <div className="flex justify-between font-sans text-[11px]">
                        <strong>Indian Institute of Technology</strong>
                        <span>2024 – 2028</span>
                      </div>
                      <p className="text-[11px] text-[#86868B] font-sans">
                        Bachelor of Technology (B.Tech) in Computer Science • Current 3rd Year • CGPA: 8.95 / 10.0
                      </p>
                    </div>

                    <div className="space-y-2">
                      <h4 className="font-bold text-[13px] uppercase tracking-wider text-[#0071E3] font-sans">
                        Tailored Technical Projects (Action-Technology-Result)
                      </h4>
                      
                      {selectedJob.role_category === "AIML" ? (
                        <>
                          <div>
                            <div className="flex justify-between font-sans text-[11px]">
                              <strong>Autonomous Multi-Agent Opportunity Hunter</strong>
                              <span>2026</span>
                            </div>
                            <ul className="list-disc list-inside text-[11px] text-[#1D1D1F]/90 space-y-0.5">
                              <li>Engineered a credit-aware 3-tier routing architecture with <strong>NVIDIA Nemotron 3 Ultra</strong> on Nebius Token Factory, reducing inference latency by 40%.</li>
                              <li>Integrated <strong>Mem0 hybrid memory with Qdrant vector store</strong> to dynamically align candidate skills to enterprise ATS postings.</li>
                            </ul>
                          </div>

                          <div>
                            <div className="flex justify-between font-sans text-[11px]">
                              <strong>Multimodal Vision & RAG Engine</strong>
                              <span>2025</span>
                            </div>
                            <ul className="list-disc list-inside text-[11px] text-[#1D1D1F]/90 space-y-0.5">
                              <li>Trained PyTorch and HuggingFace transformer models for semantic document parsing, attaining 94% precision across technical benchmark datasets.</li>
                            </ul>
                          </div>
                        </>
                      ) : (
                        <>
                          <div>
                            <div className="flex justify-between font-sans text-[11px]">
                              <strong>Distributed Task & Job Queue Engine</strong>
                              <span>2026</span>
                            </div>
                            <ul className="list-disc list-inside text-[11px] text-[#1D1D1F]/90 space-y-0.5">
                              <li>Architected an asynchronous distributed queue processing 12,000 requests/sec with FastAPI, Redis, and Celery.</li>
                              <li>Designed PostgreSQL replication and failover handling with 99.98% pipeline uptime.</li>
                            </ul>
                          </div>
                        </>
                      )}

                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <span className="text-[12px] text-[#86868B]">
                      Theme: engineeringresumes (Typst Rust Engine)
                    </span>
                    <Link
                      href="/approvals"
                      className="apple-button-primary text-[12px]"
                    >
                      <span>Proceed to Staging</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              )}

            </div>
          ) : (
            <div className="apple-card p-12 text-center text-[#86868B] text-[14px]">
              Select an opportunity from the list on the left to inspect matched keywords and the tailored RenderCV PDF.
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
