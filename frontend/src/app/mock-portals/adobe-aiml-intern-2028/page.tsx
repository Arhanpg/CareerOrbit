"use client";

import React, { useState } from "react";
import Link from "next/link";
import { CheckCircle2, Building2, MapPin, ArrowLeft, Send } from "lucide-react";
import Navigation from "@/components/Navigation";
import { getApiUrl } from "@/lib/api";

export default function MockAdobePortalPage() {
  const [formData, setFormData] = useState({
    full_name: "Arhan Praveen Ghosarwade",
    email: "arhanghosarwade05@gmail.com",
    phone: "+91 6366616225",
    institution: "Indian Institute of Information Technology (IIIT) Dharwad",
    degree: "B.Tech Computer Science and Engineering",
    graduation_batch: "2028",
    cgpa: "8.69",
    github_url: "https://github.com/Arhanpg",
    linkedin_url: "https://www.linkedin.com/in/arhan-ghosarwade-78bb16324"
  });

  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    // Simulate submission or post to backend mock portal
    try {
      const formPayload = new FormData();
      Object.entries(formData).forEach(([k, v]) => formPayload.append(k, v));
      await fetch(getApiUrl("/mock-portals/adobe-aiml-intern-2028/submit"), {
        method: "POST",
        body: formPayload
      }).catch(() => null);
    } catch {
      // ignore
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F]">
      <Navigation />

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="mb-6">
          <Link
            href="/approvals"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#86868B] hover:text-[#1D1D1F] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Approvals Studio
          </Link>
        </div>

        {submitted ? (
          <div className="apple-card p-10 text-center space-y-4">
            <div className="w-16 h-16 bg-[#E8F8EE] rounded-full flex items-center justify-center mx-auto text-[#34C759]">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#E8F8EE] text-[#1D8348]">
              Application Submitted &bull; Candidate ID: ADB-2028-9841
            </span>
            <h1 className="text-2xl font-bold text-[#1D1D1F]">Thank You for Applying to Adobe Research</h1>
            <p className="text-sm text-[#86868B] max-w-md mx-auto">
              Your application for the <strong>AI/ML Software Engineering Intern (2028 Batch)</strong> position has been received by our University Recruiting team.
            </p>
            <div className="pt-4 flex justify-center gap-3">
              <button
                onClick={() => setSubmitted(false)}
                className="apple-button-secondary text-xs"
              >
                Reset Staged Form
              </button>
              <Link
                href="/approvals"
                className="apple-button-primary text-xs"
              >
                Return to CareerOrbit
              </Link>
            </div>
          </div>
        ) : (
          <div className="apple-card overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-black/[0.06] bg-white">
              <div className="flex items-center justify-between mb-3">
                <span className="font-extrabold text-xl tracking-tight text-[#EB1000]">
                  Adobe <span className="text-[#86868B] font-normal text-xs uppercase tracking-wider ml-1">Careers Portal</span>
                </span>
                <span className="px-3 py-1 rounded-full text-[11px] font-semibold bg-[#0071E3]/10 text-[#0071E3]">
                  B.Tech 2028 Cohort
                </span>
              </div>
              <h1 className="text-xl font-bold text-[#1D1D1F]">AI/ML Software Engineering Intern (2028 Cohort)</h1>
              <div className="flex items-center gap-4 text-xs text-[#86868B] mt-1.5">
                <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" /> Adobe Systems India</span>
                <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> Bangalore / Noida, India</span>
                <span>Job ID: ADB-2028-AIML</span>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4 bg-white">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="full_name" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    Full Legal Name *
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    Email Address *
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="phone" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    Contact Phone *
                  </label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="graduation_batch" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    Graduation Batch (Year) *
                  </label>
                  <input
                    id="graduation_batch"
                    name="graduation_batch"
                    type="text"
                    required
                    value={formData.graduation_batch}
                    onChange={(e) => setFormData({ ...formData, graduation_batch: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="degree" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    Academic Degree *
                  </label>
                  <input
                    id="degree"
                    name="degree"
                    type="text"
                    required
                    value={formData.degree}
                    onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="cgpa" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    Cumulative CGPA *
                  </label>
                  <input
                    id="cgpa"
                    name="cgpa"
                    type="text"
                    required
                    value={formData.cgpa}
                    onChange={(e) => setFormData({ ...formData, cgpa: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="github_url" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    GitHub Profile URL
                  </label>
                  <input
                    id="github_url"
                    name="github_url"
                    type="url"
                    value={formData.github_url}
                    onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>

                <div>
                  <label htmlFor="linkedin_url" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                    LinkedIn Profile URL
                  </label>
                  <input
                    id="linkedin_url"
                    name="linkedin_url"
                    type="url"
                    value={formData.linkedin_url}
                    onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#F5F5F7] border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#0071E3]"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="resume_file" className="block text-xs font-semibold text-[#1D1D1F] mb-1">
                  Upload Resume (PDF, RenderCV Typst Output Attached by Agent)
                </label>
                <div className="p-4 rounded-xl bg-[#F5F5F7] border border-dashed border-black/[0.12] text-center text-xs text-[#86868B]">
                  <p className="font-medium text-[#1D1D1F]">Resume_AdobeSystemsIndia_job_adobe_aiml_2028.pdf</p>
                  <span className="text-[11px] text-[#34C759] font-medium">Pre-attached by CareerOrbit Browser Agent</span>
                </div>
              </div>

              <div className="pt-4 flex items-center justify-between border-t border-black/[0.06]">
                <span className="text-[11px] text-[#86868B]">
                  Deterministic Mock Portal for Hackathon Automated Evaluation
                </span>
                <button
                  id="submit_application_btn"
                  type="submit"
                  disabled={submitting}
                  className="apple-button-primary text-xs flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submitting ? "Submitting..." : "Submit Application"}</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}
