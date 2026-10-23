import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Triage Threads | SmartHiring Orchestrator",
  description: "Monitor autonomous rescheduling loops and negotiation threads",
};

export default function TriageThreadsPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Triage Threads" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Active Triage & Negotiation Threads
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Pemantauan alur negosiasi jadwal asinkron (maksimal 3 putaran) antara User dan Kandidat.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-warning-50 px-3 py-1 text-xs font-medium text-warning-600 dark:bg-warning-500/15 dark:text-warning-400">
            Max 3x Loop (LIMITS)
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-warning-50 text-warning-500 dark:bg-warning-500/10">
            💬
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Triage Rescheduling History
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Daftar thread negosiasi aktif beserta indikator putaran negosiasi dan eskalasi otomatis ke HR saat terjadi jalan buntu (*deadlock*).
          </p>
        </div>
      </div>
    </div>
  );
}
