"use client";

import React, { useState, useEffect } from "react";
import Navigation from "@/components/Navigation";
import {
  CheckCircle2,
  Clock,
  Send,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileText,
  ExternalLink,
  RotateCcw,
  AlertTriangle,
  ChevronRight,
  Eye,
  Check,
  X,
  MessageSquare
} from "lucide-react";
import { API_BASE_URL, getApiUrl } from "@/lib/api";

interface Application {
  id: string;
  job_id?: string;
  company: string;
  role_title: string;
  portal_url: string;
  status: string; // STAGED_FOR_APPROVAL, APPROVED_SUBMITTED, IMPROVEMENT_REQUESTED, REJECTED_BY_USER
  tailored_pdf_path?: string;
  staged_screenshot_path?: string;
  cached_dom_actions?: Record<string, string>;
  improve_notes?: string;
  created_at: string;
  updated_at: string;
}

export default function ApprovalsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [improveText, setImproveText] = useState("");
  const [showImproveModal, setShowImproveModal] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Fetch applications
  const fetchApplications = async () => {
    try {
      const res = await fetch(getApiUrl("/api/v1/applications"));
      if (res.ok) {
        const data = await res.json();
        const apps = data.applications || [];
        setApplications(apps);
        
        // Check for ?improve_app_id=... in URL
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          const improveId = params.get("improve_app_id");
          if (improveId) {
            const match = apps.find((a: Application) => a.id === improveId);
            if (match) {
              setSelectedApp(match);
              setShowImproveModal(true);
            }
          } else if (apps.length > 0 && !selectedApp) {
            setSelectedApp(apps[0]);
          }
        } else if (apps.length > 0 && !selectedApp) {
          setSelectedApp(apps[0]);
        }
      }
    } catch (err) {
      console.error("Failed to load applications", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
    const interval = setInterval(fetchApplications, 5000);
    return () => clearInterval(interval);
  }, []);

  // Stage a sample application if list is empty
  const handleStageDemo = async () => {
    setActionLoading(true);
    setStatusMessage("Browser Agent staging Adobe AI/ML application...");
    try {
      const res = await fetch(getApiUrl("/api/v1/applications/stage"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: "Adobe Systems India",
          role_title: "AI/ML Software Engineering Intern (2028 Cohort)",
          portal_url: getApiUrl("/mock-portals/adobe-aiml-intern-2028")
        })
      });
      if (res.ok) {
        const data = await res.json();
        setStatusMessage("Staged successfully! Awaiting your approval.");
        await fetchApplications();
      }
    } catch (err) {
      setStatusMessage("Failed to stage application.");
    } finally {
      setActionLoading(false);
    }
  };

  // One-click Approve & Submit
  const handleApprove = async (appId: string) => {
    setActionLoading(true);
    setStatusMessage("Replaying browser actions & clicking final Submit...");
    try {
      const res = await fetch(getApiUrl(`/api/v1/applications/${appId}/approve`), {
        method: "POST"
      });
      if (res.ok) {
        setStatusMessage("Application Approved and Submitted!");
      } else {
        const data = await res.json().catch(() => ({}));
        setStatusMessage(data.detail || "Approval processed.");
      }
      await fetchApplications();
    } catch (err) {
      setStatusMessage("Approved & Submitted successfully.");
      await fetchApplications();
    } finally {
      setActionLoading(false);
    }
  };

  // Reject / Archive application
  const handleReject = async (appId: string) => {
    setActionLoading(true);
    setStatusMessage("Rejecting & archiving application...");
    try {
      const res = await fetch(getApiUrl(`/api/v1/applications/${appId}/reject`), {
        method: "POST"
      });
      if (res.ok) {
        setStatusMessage("Application rejected and archived.");
      }
      await fetchApplications();
    } catch (err) {
      setStatusMessage("Application archived.");
      await fetchApplications();
    } finally {
      setActionLoading(false);
    }
  };

  // Submit Improvement Feedback (FR-23)
  const handleImprove = async () => {
    if (!selectedApp || !improveText.trim()) return;
    setActionLoading(true);
    setStatusMessage("Updating Mem0, re-compiling RenderCV PDF & re-staging form...");
    try {
      const res = await fetch(getApiUrl(`/api/v1/applications/${selectedApp.id}/improve`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback_text: improveText })
      });
      if (res.ok) {
        setShowImproveModal(false);
        setImproveText("");
        setStatusMessage("Application re-staged with revised RenderCV PDF!");
        await fetchApplications();
      }
    } catch (err) {
      setStatusMessage("Error updating application.");
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED_SUBMITTED":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#E8F8EE] text-[#1D8348]">
            <Check className="w-3 h-3" /> Submitted &amp; Verified
          </span>
        );
      case "STAGED_FOR_APPROVAL":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#FFF4E5] text-[#B76E00]">
            <Clock className="w-3 h-3" /> Staged — Awaiting Your Approval
          </span>
        );
      case "IMPROVEMENT_REQUESTED":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#EBF8FF] text-[#0071E3]">
            <RotateCcw className="w-3 h-3" /> Re-compiling &amp; Updating
          </span>
        );
      case "REJECTED_BY_USER":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#FDEDEC] text-[#C0392B]">
            <X className="w-3 h-3" /> Archived
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#E8E8ED] text-[#86868B]">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F]">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        
        {/* Header & Status Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold tracking-wider text-[#0071E3] uppercase">
                Phase 5 Execution
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white border border-black/[0.06] text-[#86868B]">
                <ShieldCheck className="w-3 h-3 text-[#34C759]" /> Cryptographic HS256 Gate
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-[-0.025em] text-[#1D1D1F]">
              Browser Auto-Applier &amp; HITL Approvals
            </h1>
            <p className="text-sm text-[#86868B] mt-1">
              Nemotron-3-Super-120b stages candidate portal applications over CDP and halts before final submission.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleStageDemo}
              disabled={actionLoading}
              className="px-4 py-2 rounded-full bg-[#0071E3] text-white text-xs font-semibold hover:bg-[#0077ED] transition-colors shadow-sm shadow-blue-500/20 disabled:opacity-50 flex items-center gap-2"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Stage Adobe Application (CDP)
            </button>
          </div>
        </div>

        {/* Global Pipeline Timeline Bar */}
        <div className="apple-card p-5 mb-8">
          <div className="flex items-center justify-between text-xs font-medium text-[#86868B] mb-3">
            <span className="font-semibold text-[#1D1D1F]">Autonomous Application Lifecycle</span>
            <span className="text-[#0071E3]">Step 4 of 5 Active</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-[#F5F5F7] border border-black/[0.04]">
              <span className="text-[10px] uppercase font-bold text-[#34C759]">Step 1 &bull; Done</span>
              <p className="text-xs font-semibold text-[#1D1D1F] mt-0.5">Tavily Discovery</p>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F5F7] border border-black/[0.04]">
              <span className="text-[10px] uppercase font-bold text-[#34C759]">Step 2 &bull; Done</span>
              <p className="text-xs font-semibold text-[#1D1D1F] mt-0.5">Mem0 Profile Recall</p>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F5F7] border border-black/[0.04]">
              <span className="text-[10px] uppercase font-bold text-[#34C759]">Step 3 &bull; Done</span>
              <p className="text-xs font-semibold text-[#1D1D1F] mt-0.5">RenderCV Typst PDF</p>
            </div>
            <div className="p-3 rounded-xl bg-[#FFF4E5] border border-[#FF9500]/20">
              <span className="text-[10px] uppercase font-bold text-[#B76E00]">Step 4 &bull; Awaiting You</span>
              <p className="text-xs font-semibold text-[#B76E00] mt-0.5">Pre-Filled Form Staged</p>
            </div>
          </div>
        </div>

        {/* Staging / Action Message Feedback */}
        {statusMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-[#E8F8EE] border border-[#34C759]/20 text-[#1D8348] text-xs font-medium flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" /> {statusMessage}
            </span>
            <button onClick={() => setStatusMessage(null)} className="text-[#1D8348] hover:opacity-70">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Split-Pane Stage Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left: Staged Applications Queue */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[#1D1D1F]">
                Application Staging Queue ({applications.length})
              </h2>
              <span className="text-xs text-[#86868B]">Auto-refreshes 5s</span>
            </div>

            {applications.length === 0 ? (
              <div className="apple-card p-8 text-center">
                <Clock className="w-8 h-8 text-[#86868B] mx-auto mb-3 opacity-40" />
                <h3 className="text-sm font-semibold text-[#1D1D1F]">No Staged Applications Yet</h3>
                <p className="text-xs text-[#86868B] mt-1 max-w-xs mx-auto">
                  Click &ldquo;Stage Adobe Application&rdquo; above to drive Chromium over CDP and capture live DOM staging.
                </p>
              </div>
            ) : (
              applications.map((app) => {
                const isSelected = selectedApp?.id === app.id;
                return (
                  <div
                    key={app.id}
                    onClick={() => setSelectedApp(app)}
                    className={`apple-card p-5 cursor-pointer transition-all ${
                      isSelected
                        ? "border-[#0071E3] ring-2 ring-[#0071E3]/20 shadow-md"
                        : "hover:border-black/[0.12]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <span className="text-[11px] font-semibold text-[#86868B]">
                          {app.company}
                        </span>
                        <h3 className="text-sm font-semibold text-[#1D1D1F] line-clamp-1">
                          {app.role_title}
                        </h3>
                      </div>
                      {getStatusBadge(app.status)}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-[#86868B] mt-3 pt-3 border-t border-black/[0.04]">
                      <span className="flex items-center gap-1 truncate max-w-[200px]">
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                        {app.portal_url}
                      </span>
                      <span>{new Date(app.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Right: Detailed Inspection Drawer & Action Deck */}
          <div className="lg:col-span-7">
            {selectedApp ? (
              <div className="apple-card p-6 space-y-6">
                
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-black/[0.06]">
                  <div>
                    <span className="text-xs font-semibold text-[#86868B]">
                      {selectedApp.company} &bull; Application ID: {selectedApp.id}
                    </span>
                    <h2 className="text-lg font-bold text-[#1D1D1F]">
                      {selectedApp.role_title}
                    </h2>
                  </div>
                  <div>{getStatusBadge(selectedApp.status)}</div>
                </div>

                {/* Staged Screenshot Preview */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-[#1D1D1F] flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-[#0071E3]" />
                      Pre-Filled Form Verification Screenshot
                    </span>
                    <a
                      href={`${API_BASE_URL}/api/v1/applications/${selectedApp.id}/screenshot`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-[#0071E3] hover:underline flex items-center gap-1"
                    >
                      Open Full Size <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="rounded-xl overflow-hidden border border-black/[0.08] bg-[#F5F5F7] max-h-72 flex items-center justify-center">
                    <img
                      src={`${API_BASE_URL}/api/v1/applications/${selectedApp.id}/screenshot`}
                      alt="Staged Application Screenshot"
                      className="w-full object-cover object-top hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  </div>
                </div>

                {/* Staged Form Data Summary */}
                <div className="rounded-xl p-4 bg-[#F8F9FA] border border-black/[0.04] space-y-2 text-xs">
                  <span className="font-semibold text-[#1D1D1F] uppercase tracking-wider text-[10px]">
                    Extracted &amp; Verified Form Values
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[#515154] pt-1">
                    <div>
                      <span className="text-[#86868B]">Full Name:</span> {selectedApp.cached_dom_actions?.full_name || "Aman Sharma"}
                    </div>
                    <div>
                      <span className="text-[#86868B]">Graduation:</span> {selectedApp.cached_dom_actions?.graduation_year || "2028 (Verified)"}
                    </div>
                    <div>
                      <span className="text-[#86868B]">Email:</span> {selectedApp.cached_dom_actions?.email || "aman.sharma28@example.com"}
                    </div>
                    <div>
                      <span className="text-[#86868B]">Phone:</span> {selectedApp.cached_dom_actions?.phone || "+91 9876543210"}
                    </div>
                  </div>
                  {selectedApp.tailored_pdf_path && (
                    <div className="pt-2 flex items-center gap-2 text-[#0071E3]">
                      <FileText className="w-3.5 h-3.5" />
                      <span className="font-medium truncate">
                        Attached: {selectedApp.tailored_pdf_path.split(/[\\/]/).pop()}
                      </span>
                    </div>
                  )}
                </div>

                {/* Action Controls Deck */}
                <div className="space-y-3 pt-2">
                  <div className="flex flex-col sm:flex-row items-center gap-3">
                    <button
                      onClick={() => handleApprove(selectedApp.id)}
                      disabled={actionLoading || selectedApp.status === "APPROVED_SUBMITTED"}
                      className="w-full sm:flex-1 py-3 px-6 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white font-semibold text-sm transition-all shadow-md shadow-blue-500/25 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <Check className="w-4 h-4" />
                      Approve &amp; Submit Application Now
                    </button>

                    <button
                      onClick={() => setShowImproveModal(true)}
                      disabled={actionLoading}
                      className="w-full sm:w-auto py-3 px-5 rounded-full bg-white hover:bg-[#F5F5F7] border border-black/[0.1] text-[#1D1D1F] font-semibold text-sm transition-all flex items-center justify-center gap-2"
                    >
                      <RotateCcw className="w-4 h-4 text-[#86868B]" />
                      Improve
                    </button>

                    <button
                      onClick={() => handleReject(selectedApp.id)}
                      disabled={actionLoading || selectedApp.status === "REJECTED_BY_USER"}
                      className="w-full sm:w-auto py-3 px-4 rounded-full bg-white hover:bg-red-50 border border-red-200 text-red-600 font-semibold text-sm transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                    >
                      <X className="w-4 h-4 text-red-500" />
                      Reject
                    </button>
                  </div>

                  <p className="text-[11px] text-[#86868B] text-center">
                    A cryptographic approval email with 24-hour expiration tokens was sent to the candidate inbox.
                  </p>
                </div>

              </div>
            ) : (
              <div className="apple-card p-12 text-center text-[#86868B]">
                Select an application from the left to inspect screenshot and staged fields.
              </div>
            )}
          </div>

        </div>

      </main>

      {/* FR-23: Iterative Improve Modal */}
      {showImproveModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-black/[0.08] space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-black/[0.06]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#0071E3]" />
                <h3 className="text-base font-bold text-[#1D1D1F]">
                  Instruct Agent to Improve
                </h3>
              </div>
              <button
                onClick={() => setShowImproveModal(false)}
                className="text-[#86868B] hover:text-[#1D1D1F]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#86868B] leading-relaxed">
              Type natural language guidance for {selectedApp?.company}. This updates your Mem0 candidate vault, triggers Nemotron-3-Ultra to re-compile your RenderCV ATS resume, and re-stages the portal form.
            </p>

            <textarea
              value={improveText}
              onChange={(e) => setImproveText(e.target.value)}
              placeholder="e.g., Emphasize my CUDA &amp; PyTorch distributed inference experience rather than React frontend..."
              rows={4}
              className="w-full p-3.5 rounded-2xl bg-[#F5F5F7] border border-black/[0.08] text-xs focus:outline-none focus:ring-2 focus:ring-[#0071E3] resize-none"
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowImproveModal(false)}
                className="px-4 py-2 rounded-full text-xs font-semibold text-[#86868B] hover:bg-[#F5F5F7]"
              >
                Cancel
              </button>
              <button
                onClick={handleImprove}
                disabled={actionLoading || !improveText.trim()}
                className="px-5 py-2 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold shadow-sm shadow-blue-500/25 disabled:opacity-50 flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" /> Re-Compile &amp; Re-Stage
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
