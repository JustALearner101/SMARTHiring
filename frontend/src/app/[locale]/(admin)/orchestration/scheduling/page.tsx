import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Autonomous Scheduling | SmartHiring Orchestrator",
  description: "Autonomous Interview Scheduling & Human Approval Gate (HITL)",
};

export default function AutonomousSchedulingPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Autonomous Scheduling" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Autonomous Scheduling & Action Plans
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Hero Feature: Orkestrasi eskalasi kandidat ke User Interview dengan Human-in-the-Loop (HITL) Approval & 60s Undo Window.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
            Pilar: APPROVAL & LIMITS
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-500/10">
            ⚡
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Confirmation Screen & Triage Buffer
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Kartu konfirmasi aksi (*ActionPlan Confirmation Card*), sitasi sumber (*SOURCES Cited*), deteksi ambiguitas nama, dan tombol pembatalan 60 detik akan dirender di sini.
          </p>
        </div>
      </div>
    </div>
  );
}
