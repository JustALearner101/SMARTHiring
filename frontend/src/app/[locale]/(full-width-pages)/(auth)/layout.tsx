import GridShape from "@/components/common/GridShape";
import ThemeTogglerTwo from "@/components/common/ThemeTogglerTwo";
import { ThemeProvider } from "@/context/ThemeContext";
import { Link } from "@/i18n/navigation";
import Image from "next/image";
import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative p-6 bg-white z-1 dark:bg-gray-900 sm:p-0">
      <ThemeProvider>
        <div className="relative flex lg:flex-row w-full h-screen justify-center flex-col dark:bg-gray-900 sm:p-0">
          {children}

          {/* Right Pane */}
          <div className="lg:w-1/2 w-full h-full bg-brand-950 dark:bg-brand-950 lg:flex flex-col justify-between p-8 xl:p-12 hidden relative overflow-hidden select-none">
            {/* Background Decor & Ambient Glow */}
            <GridShape />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[520px] h-[520px] bg-brand-500/15 rounded-full blur-3xl pointer-events-none" />

            {/* Top: Brand Header */}
            <div className="relative z-10 flex items-center justify-between">
              <Link href="/" className="inline-block transition-opacity hover:opacity-90">
                <Image
                  src="/images/logo/logo-dark.svg"
                  alt="SmartHiring Logo"
                  width={200}
                  height={58}
                  className="h-15 w-auto object-contain"
                  priority
                />
              </Link>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-500/15 border border-brand-400/25 px-3 py-1 text-xs font-medium text-brand-300 backdrop-blur-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Next-Gen AI HR Agent
              </span>
            </div>

            {/* Center: Hero Illustration + Floating Micro-Cards */}
            <div className="relative z-10 my-auto flex flex-col items-center justify-center py-6">
              <div className="relative w-full max-w-[460px] xl:max-w-[510px]">
                {/* Floating Micro-Card 1: Interview Scheduled (Top-Left) */}
                <div className="absolute -top-4 -left-4 z-20 flex items-center gap-3 rounded-2xl border border-white/15 bg-brand-900/95 px-3.5 py-2.5 shadow-2xl backdrop-blur-md transition-all duration-300 hover:-translate-y-1">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 shadow-inner">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="text-start">
                    <p className="text-xs font-semibold text-white tracking-wide">Interview Confirmed</p>
                    <p className="text-[11px] text-gray-300">Technical Round • 14:00 WIB</p>
                  </div>
                </div>

                {/* Main Illustration Container */}
                <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl backdrop-blur-md">
                  <Image
                    src="/images/9650007_7566.svg"
                    alt="SmartHiring Interview Orchestration"
                    width={800}
                    height={500}
                    className="w-full h-auto object-contain rounded-2xl drop-shadow-md"
                    priority
                  />
                </div>

                {/* Floating Micro-Card 2: Copilot Active (Bottom-Right) */}
                <div className="absolute -bottom-4 -right-4 z-20 flex items-center gap-3 rounded-2xl border border-white/15 bg-brand-900/95 px-3.5 py-2.5 shadow-2xl backdrop-blur-md transition-all duration-300 hover:translate-y-1">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/25 text-brand-400 shadow-inner">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div className="text-start">
                    <p className="text-xs font-semibold text-white tracking-wide">Copilot Active</p>
                    <p className="text-[11px] text-emerald-400 font-medium">94% Cited Rubric Evidence</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom: Value Proposition & Feature Pills */}
            <div className="relative z-10 text-center max-w-lg mx-auto">
              <h2 className="text-lg xl:text-xl font-bold text-white mb-2 tracking-tight">
                Autonomous Interview Triaging & Copilot
              </h2>
              <p className="text-xs text-gray-300 leading-relaxed mb-4">
                Automated triage scheduling via WhatsApp and email, with a guarantee of human approval and evidence-based, objective competency evaluation.
              </p>
              <div className="flex items-center justify-center gap-2 flex-wrap text-[11px] text-gray-300">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 border border-white/10 px-3 py-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                  Zero-Trust Human Gate
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 border border-white/10 px-3 py-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-400"></span>
                  60s Undo Window
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 border border-white/10 px-3 py-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
                  100% Cited Copilot
                </span>
              </div>
            </div>
          </div>

          {/* Theme Toggler */}
          <div className="fixed bottom-6 right-6 z-50 hidden sm:block">
            <ThemeTogglerTwo />
          </div>
        </div>
      </ThemeProvider>
    </div>
  );
}
