import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Interviewer Email Simulator | SmartHiring Orchestrator",
  description: "Interactive email client simulator for Hiring Managers to test interview invitations and replies",
};

export default function InterviewerEmailSimulatorPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Interviewer Email Simulator" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Interviewer Email Simulator (In-App Webmail)
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Simulasi inbox email resmi Hiring Manager untuk menguji penerimaan draf undangan dan balasan ketersediaan jadwal saat Live Demo 90 Detik.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
            Demo Day Ready
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-500/10">
            ✉️
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Simulated Inbox & Reply Trigger
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Lihat email yang dikirim AI, baca ringkasan profil kandidat, dan balas dengan opsi jadwal baru untuk memicu autonomous triage tanpa delay SMTP.
          </p>
        </div>
      </div>
    </div>
  );
}
