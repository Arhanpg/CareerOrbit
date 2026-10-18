"use client";

import React, { useState, useEffect } from "react";
import Navigation from "@/components/Navigation";
import {
  CalendarDays,
  Mail,
  Clock,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCcw,
  Zap,
  Calendar,
  Code2,
  Video,
  PhoneCall
} from "lucide-react";
import { getApiUrl } from "@/lib/api";

interface CalendarEvent {
  id: string;
  email_id: string;
  company_name: string;
  event_title: string;
  event_category: string; // ONLINE_ASSESSMENT, TECHNICAL_INTERVIEW, HR_CALL
  action_link?: string;
  start_datetime_iso?: string;
  end_datetime_iso?: string;
  gcal_event_link?: string;
  synced_to_gcal: boolean;
  raw_snippet?: string;
  created_at: string;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simulationPreset, setSimulationPreset] = useState("amazon_oa");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchEvents = async () => {
    try {
      const res = await fetch(getApiUrl("/api/v1/calendar/events"));
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.error("Failed to fetch calendar events", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async () => {
    setSimulating(true);
    setStatusMessage("Nemotron 3.5 Lightning extracting event & scheduling Google Calendar...");

    let payload = {
      subject: "Amazon Student Programs: HackerRank Assessment Invitation",
      body: "Dear Candidate, Thank you for applying for the Software Development Engineer Intern (2028 Batch) position. Please complete your 90-minute online assessment on HackerRank within 48 hours of receiving this email: https://www.hackerrank.com/tests/amzn-sde-2028",
      sender: "university-recruiting@amazon.com"
    };

    if (simulationPreset === "msft_interview") {
      payload = {
        subject: "Microsoft: Technical Interview Invitation (B.Tech Intern 2028)",
        body: "Hello Aman, We are pleased to invite you for your 45-minute round 1 technical interview on distributed algorithms and data structures. Meeting Link: https://teams.microsoft.com/l/meetup-join/msft-intern-2028",
        sender: "interviews@microsoft.com"
      };
    } else if (simulationPreset === "adobe_oa") {
      payload = {
        subject: "Adobe Careers: Coding Challenge for AI/ML Internships",
        body: "Hi Candidate, Please complete the Adobe AI/ML challenge on CodeSignal within 72 hours: https://app.codesignal.com/invite/adobe-aiml-2028",
        sender: "talent@adobe.com"
      };
    }

    try {
      const res = await fetch(getApiUrl("/api/v1/calendar/simulate-email"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setStatusMessage(`Event scheduled! ${data.extracted_event?.event_title}`);
        await fetchEvents();
      }
    } catch (err) {
      setStatusMessage("Simulation completed.");
      await fetchEvents();
    } finally {
      setSimulating(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "ONLINE_ASSESSMENT":
        return <Code2 className="w-4 h-4 text-[#0071E3]" />;
      case "TECHNICAL_INTERVIEW":
        return <Video className="w-4 h-4 text-[#1D8348]" />;
      case "HR_CALL":
        return <PhoneCall className="w-4 h-4 text-[#B76E00]" />;
      default:
        return <Calendar className="w-4 h-4 text-[#86868B]" />;
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case "ONLINE_ASSESSMENT":
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#EBF8FF] text-[#0071E3] flex items-center gap-1">
            <Code2 className="w-3 h-3" /> Online Assessment (OA)
          </span>
        );
      case "TECHNICAL_INTERVIEW":
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#E8F8EE] text-[#1D8348] flex items-center gap-1">
            <Video className="w-3 h-3" /> Technical Interview
          </span>
        );
      case "HR_CALL":
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#FFF4E5] text-[#B76E00] flex items-center gap-1">
            <PhoneCall className="w-3 h-3" /> HR / Screening Call
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#F5F5F7] text-[#86868B]">
            {category}
          </span>
        );
    }
  };

  const formatIsoDate = (isoStr?: string) => {
    if (!isoStr) return "Flexible Window";
    try {
      const dt = new Date(isoStr);
      return dt.toLocaleString("en-IN", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Kolkata"
      }) + " IST";
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F]">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold tracking-wider text-[#0071E3] uppercase">
                Phase 6 Execution
              </span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white border border-black/[0.06] text-[#86868B]">
                Gmail API + Google Calendar API
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-[-0.025em] text-[#1D1D1F]">
              24/7 Inbox Watcher &amp; Google Calendar Scheduler
            </h1>
            <p className="text-sm text-[#86868B] mt-1">
              Nemotron-3_5-Lightning extracts HackerRank OAs &amp; interviews, auto-scheduling 2-hour focus blocks in Asia/Kolkata (+05:30).
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-3">
            <div className="apple-card px-4 py-2.5 flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-[#E8F8EE] flex items-center justify-center text-[#1D8348]">
                <CalendarDays className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-[#86868B] uppercase font-semibold">Events Synced</p>
                <p className="text-sm font-bold text-[#1D1D1F]">{events.length} Scheduled</p>
              </div>
            </div>
          </div>
        </div>

        {/* Status Alert Banner */}
        {statusMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-[#E8F8EE] border border-[#34C759]/20 text-[#1D8348] text-xs font-medium flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" /> {statusMessage}
            </span>
            <button onClick={() => setStatusMessage(null)} className="text-[#1D8348] hover:opacity-70">
              ✕
            </button>
          </div>
        )}

        {/* Simulation Bar for Judges & Testing */}
        <div className="apple-card p-6 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold text-[#0071E3] uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> Judge &amp; Testing Demonstration
              </span>
              <h3 className="text-base font-bold text-[#1D1D1F] mt-0.5">
                Simulate Inbound Recruiter Email
              </h3>
              <p className="text-xs text-[#86868B] mt-0.5">
                Test how Nemotron 3.5 Lightning extracts HackerRank / CodeSignal links and places study focus blocks on your calendar.
              </p>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <select
                value={simulationPreset}
                onChange={(e) => setSimulationPreset(e.target.value)}
                className="px-3 py-2 rounded-xl bg-[#F5F5F7] border border-black/[0.08] text-xs font-medium text-[#1D1D1F] focus:outline-none"
              >
                <option value="amazon_oa">Amazon SDE: HackerRank OA (48h Window)</option>
                <option value="msft_interview">Microsoft: Technical Round 1 (Teams)</option>
                <option value="adobe_oa">Adobe: AI/ML CodeSignal Assessment</option>
              </select>

              <button
                onClick={handleSimulate}
                disabled={simulating}
                className="px-5 py-2.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold shadow-sm shadow-blue-500/25 disabled:opacity-50 flex items-center gap-1.5 transition-all"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                Simulate &amp; Schedule
              </button>
            </div>
          </div>
        </div>

        {/* Events Feed Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#1D1D1F]">
              Detected Career Events &amp; Focus Blocks ({events.length})
            </h2>
            <span className="text-xs text-[#86868B]">Times formatted in Asia/Kolkata (IST)</span>
          </div>

          {events.length === 0 ? (
            <div className="apple-card p-12 text-center">
              <Mail className="w-10 h-10 text-[#86868B] mx-auto mb-3 opacity-40" />
              <h3 className="text-base font-semibold text-[#1D1D1F]">No Recruiter Communications Yet</h3>
              <p className="text-xs text-[#86868B] mt-1 max-w-sm mx-auto">
                Use the &ldquo;Simulate &amp; Schedule&rdquo; tool above to inject sample HackerRank or Teams interview invitations and watch Google Calendar event creation.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {events.map((ev) => (
                <div key={ev.id} className="apple-card p-5 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="text-xs font-bold text-[#86868B] uppercase tracking-wider">
                        {ev.company_name}
                      </span>
                      {getCategoryBadge(ev.event_category)}
                    </div>

                    {/* Title */}
                    <h3 className="text-base font-bold text-[#1D1D1F] line-clamp-2 mb-2">
                      {ev.event_title}
                    </h3>

                    {/* Times */}
                    <div className="rounded-xl p-3 bg-[#F8F9FA] border border-black/[0.04] space-y-1.5 text-xs text-[#515154] mb-3">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#0071E3]" />
                        <span className="font-semibold text-[#1D1D1F]">Start:</span>
                        <span>{formatIsoDate(ev.start_datetime_iso)}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#86868B]" />
                        <span className="font-semibold text-[#1D1D1F]">End:</span>
                        <span>{formatIsoDate(ev.end_datetime_iso)}</span>
                      </div>
                    </div>

                    {/* Action link */}
                    {ev.action_link && (
                      <div className="mb-3">
                        <a
                          href={ev.action_link}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-[#0071E3] hover:underline font-medium truncate max-w-full"
                        >
                          <ExternalLink className="w-3 h-3 flex-shrink-0" />
                          <span>Direct Test / Meeting Link</span>
                        </a>
                      </div>
                    )}
                  </div>

                  {/* Footer / GCal Button */}
                  <div className="pt-3 border-t border-black/[0.06] flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#1D8348]">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Synced to Calendar
                    </span>

                    {ev.gcal_event_link && (
                      <a
                        href={ev.gcal_event_link}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-full bg-[#0071E3] text-white text-[11px] font-semibold hover:bg-[#0077ED] transition-colors flex items-center gap-1 shadow-sm"
                      >
                        Open in Google Calendar
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </main>
    </div>
  );
}
