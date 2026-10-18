"use client";

import React, { useState, useEffect } from "react";
import { 
  BrainCircuit, 
  Upload, 
  Send, 
  FileText, 
  CheckCircle2, 
  Sparkles, 
  Filter, 
  Layers, 
  PlusCircle, 
  Tag, 
  Check,
  AlertCircle
} from "lucide-react";

export default function MemoryVaultPage() {
  // Constraints form state
  const [profile, setProfile] = useState<any>({
    full_name: "Aman Sharma",
    email: "aman.sharma28@example.com",
    phone: "+91 9876543210",
    current_location: "India",
    degree: "B.Tech",
    graduation_batch: 2028,
    current_academic_year: "3rd Year",
    cgpa: 8.95,
    target_roles: ["SDE Intern", "AI/ML Intern", "Backend Developer", "Hackathon"],
    allowed_locations: ["India", "Remote", "Bangalore", "Hyderabad", "Pune"],
    github_url: "https://github.com/amansharma28",
    linkedin_url: "https://linkedin.com/in/amansharma28",
    portfolio_url: "https://amansharma.dev",
    address_line: "Koramangala 4th Block, Bangalore",
    postal_code: "560034"
  });

  const [memories, setMemories] = useState<any[]>([]);
  const [selectedFilter, setSelectedFilter] = useState("ALL");
  const [chatInput, setChatInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isSavingConstraints, setIsSavingConstraints] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Fetch initial data
  useEffect(() => {
    fetchProfile();
    fetchMemories();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/profile/constraints");
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch (err) {
      console.log("Running local mock constraints");
    }
  };

  const fetchMemories = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/memory/all");
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories || []);
      }
    } catch (err) {
      console.log("Running local mock memories");
    }
  };

  const handleSaveConstraints = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingConstraints(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/profile/constraints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile)
      });
      if (res.ok) {
        setNotification("Candidate constraints saved to Master Vault (SQLite).");
        setTimeout(() => setNotification(null), 3500);
      }
    } catch (err) {
      setNotification("Failed to save constraints to backend.");
    } finally {
      setIsSavingConstraints(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setIsUploading(true);
    const formData = new FormData();
    for (let i = 0; i < e.target.files.length; i++) {
      formData.append("files", e.target.files[i]);
    }
    formData.append("user_id", "default_user");

    try {
      const res = await fetch("http://localhost:8000/api/v1/memory/upload-files", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setNotification(`Extracted ${data.total_facts_stored} facts from ${data.files_processed} files into Mem0.`);
        fetchMemories();
        setTimeout(() => setNotification(null), 4000);
      }
    } catch (err) {
      setNotification("Upload failed. Make sure backend is running.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleChatUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    try {
      const res = await fetch("http://localhost:8000/api/v1/memory/chat-update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: chatInput, user_id: "default_user" })
      });
      if (res.ok) {
        setChatInput("");
        setNotification("New atomic memory fact synthesized by Nemotron 3.5 Lightning.");
        fetchMemories();
        setTimeout(() => setNotification(null), 3500);
      }
    } catch (err) {
      setNotification("Could not send chat update.");
    }
  };

  const filteredMemories = memories.filter((m) => {
    if (selectedFilter === "ALL") return true;
    return m.category.toUpperCase() === selectedFilter;
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-2xl bg-[#1D1D1F] text-white text-[13px] font-medium shadow-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#34C759]" />
          <span>{notification}</span>
        </div>
      )}

      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide bg-[#0071E3]/10 text-[#0071E3] uppercase">
            Plane 1: Core Memory Vault
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#E8F8EE] text-[#1D8348]">
            Mem0 + Local Qdrant Engine
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-[-0.025em] text-[#1D1D1F] mt-1.5">
          Candidate Memory & Constraint Studio
        </h1>
        <p className="text-[14px] text-[#86868B] max-w-3xl mt-1">
          Upload multiple resumes (SDE, AI/ML, hackathons) or type natural language accomplishments. Mem0 automatically links technologies, quantified impact metrics, and projects into an evolving vector store powered by Nebius Token Factory.
        </p>
      </div>

      {/* Top 2 Columns: Constraints + Dropzone & Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left: Canonical Constraints Form */}
        <div className="apple-card p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-black/[0.06]">
            <div>
              <h2 className="font-semibold text-[16px] text-[#1D1D1F]">
                Candidate Hard Constraints (Master Vault)
              </h2>
              <p className="text-[12px] text-[#86868B]">Deterministic ground truth for form auto-fills</p>
            </div>
            <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-[#E8F8EE] text-[#1D8348]">
              Batch 2028 Enforced
            </span>
          </div>

          <form onSubmit={handleSaveConstraints} className="space-y-4 text-[13px]">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  Full Legal Name
                </label>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  Degree
                </label>
                <input
                  type="text"
                  value={profile.degree}
                  onChange={(e) => setProfile({ ...profile, degree: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  Graduation Batch
                </label>
                <input
                  type="number"
                  value={profile.graduation_batch}
                  onChange={(e) => setProfile({ ...profile, graduation_batch: parseInt(e.target.value) || 2028 })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  CGPA (Scale 10)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={profile.cgpa}
                  onChange={(e) => setProfile({ ...profile, cgpa: parseFloat(e.target.value) || 0.0 })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  GitHub Profile
                </label>
                <input
                  type="url"
                  value={profile.github_url}
                  onChange={(e) => setProfile({ ...profile, github_url: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-[#86868B] uppercase tracking-wider mb-1">
                  LinkedIn Profile
                </label>
                <input
                  type="url"
                  value={profile.linkedin_url}
                  onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-black/[0.08] focus:border-[#0071E3] focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSavingConstraints}
              className="w-full apple-button-primary justify-center mt-2"
            >
              <Check className="w-4 h-4" />
              <span>{isSavingConstraints ? "Saving to Vault..." : "Save Canonical Constraints"}</span>
            </button>
          </form>
        </div>

        {/* Right: Multi-File Resume Dropzone & Live Chat Updater */}
        <div className="space-y-6">
          
          {/* File Dropzone */}
          <div className="apple-card p-6 space-y-3">
            <h2 className="font-semibold text-[16px] text-[#1D1D1F]">
              Multi-File Resume Dropzone
            </h2>
            <p className="text-[12px] text-[#86868B]">
              Drop your SDE Resume, AI/ML Resume, and project notes (PDF, DOCX, TXT, MD). Mem0 parses atomic achievements automatically.
            </p>
            
            <label className="border-2 border-dashed border-black/[0.1] hover:border-[#0071E3] rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors bg-[#F5F5F7]/50 hover:bg-blue-50/20">
              <Upload className="w-7 h-7 text-[#0071E3] mb-2" />
              <span className="text-[13px] font-medium text-[#1D1D1F]">
                {isUploading ? "Extracting & Vectorizing into Mem0..." : "Click or drag resume files here"}
              </span>
              <span className="text-[11px] text-[#86868B] mt-1">Supports multiple files simultaneously</span>
              <input 
                type="file" 
                multiple 
                accept=".pdf,.docx,.txt,.md" 
                className="hidden" 
                onChange={handleFileUpload}
                disabled={isUploading}
              />
            </label>
          </div>

          {/* Talk to Core Memory Chat Bar */}
          <div className="apple-card p-6 space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#0071E3]" />
              <h2 className="font-semibold text-[16px] text-[#1D1D1F]">
                Talk to Core Memory (Additive Updates)
              </h2>
            </div>
            <p className="text-[12px] text-[#86868B]">
              Add accomplishments on the fly (e.g., "Just deployed an agent with Nemotron 3 Ultra cutting latency by 40%").
            </p>

            <form onSubmit={handleChatUpdate} className="flex gap-2">
              <input
                type="text"
                placeholder="Type new accomplishment, project, or metric..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                className="flex-1 px-4 py-2.5 rounded-full border border-black/[0.08] text-[13px] focus:outline-none focus:border-[#0071E3] bg-[#F5F5F7]"
              />
              <button
                type="submit"
                className="apple-button-primary px-5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Add Fact</span>
              </button>
            </form>
          </div>

        </div>

      </div>

      {/* Bottom Section: Extracted Atomic Memory Cards */}
      <div className="apple-card p-6 sm:p-7 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-black/[0.06]">
          <div>
            <div className="flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-[#0071E3]" />
              <h2 className="text-lg font-semibold tracking-[-0.015em] text-[#1D1D1F]">
                Extracted Atomic Memory Cards
              </h2>
            </div>
            <p className="text-[13px] text-[#86868B] mt-0.5">
              Self-improving semantic memories linked via Mem0 + Qdrant. Retrieved dynamically for each target opportunity.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 apple-segmented-nav">
            {["ALL", "PROJECT", "SKILL", "INTERNSHIP", "METRIC"].map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedFilter(cat)}
                className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${
                  selectedFilter === cat
                    ? "bg-white text-[#1D1D1F] shadow-sm"
                    : "text-[#86868B] hover:text-[#1D1D1F]"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMemories.length === 0 ? (
            <div className="col-span-full py-12 text-center text-[#86868B] text-[13px]">
              No atomic memories found. Upload your resumes above or type a project into "Talk to Memory".
            </div>
          ) : (
            filteredMemories.map((mem) => {
              const isProject = mem.category === "PROJECT";
              const isMetric = mem.category === "METRIC";
              const isInternship = mem.category === "INTERNSHIP";
              return (
                <div
                  key={mem.id}
                  className="p-4 rounded-2xl bg-[#F5F5F7] border border-black/[0.04] space-y-2 hover:bg-white hover:border-black/[0.08] hover:shadow-sm transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      isProject ? "bg-blue-100 text-[#0071E3]" :
                      isMetric ? "bg-emerald-100 text-[#1D8348]" :
                      isInternship ? "bg-purple-100 text-purple-700" :
                      "bg-[#E8E8ED] text-[#1D1D1F]"
                    }`}>
                      {mem.category}
                    </span>
                    <span className="text-[11px] text-[#86868B]">
                      {mem.source || "User Update"}
                    </span>
                  </div>

                  <p className="text-[13px] text-[#1D1D1F] leading-relaxed">
                    {mem.content}
                  </p>

                  <div className="pt-2 border-t border-black/[0.04] flex items-center justify-between text-[11px] text-[#86868B]">
                    <span>Qdrant Vector Indexed</span>
                    <span>Class of 2028</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

      </div>

    </div>
  );
}
