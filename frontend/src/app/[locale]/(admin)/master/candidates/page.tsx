import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Candidate Directory | SmartHiring Orchestrator",
  description: "Candidate applications, contact channels, and timezone directory",
};

export default function CandidatesPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Candidates" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Candidate Applications Directory
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Master data pelamar: Channel kontak preferensi (WhatsApp/Email), resume link, status aplikasi, dan zona waktu domisili.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            Master Data
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            👥
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Candidates Table & Quick Actions
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Kelola data kandidat (`tblm_candidate`), filter status pipeline rekrutmen, dan tombol aksi cepat &quot;Eskalasi ke Jadwal Interview&quot;.
          </p>
        </div>
      </div>
    </div>
  );
}
