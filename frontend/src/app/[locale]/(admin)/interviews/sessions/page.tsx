import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Interview Sessions | SmartHiring Orchestrator",
  description: "Manage interview sessions, consent verification, and audio/note upload",
};

export default function InterviewSessionsPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Interview Sessions" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Interview Sessions & Audio Upload
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Daftar sesi wawancara, unggah rekaman audio/dokumen catatan, dan verifikasi status persetujuan kandidat (*Consent Check*).
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-blue-light-50 px-3 py-1 text-xs font-medium text-blue-light-600 dark:bg-blue-light-500/15 dark:text-blue-light-400">
            Consent Verifier
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-light-50 text-blue-light-500 dark:bg-blue-light-500/10">
            🎙️
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Interview Sessions Table & Ingestion
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Tabel sesi wawancara (`tblt_interview`), unggah rekaman (`tblt_source_file`), dan pemrosesan job transkripsi.
          </p>
        </div>
      </div>
    </div>
  );
}
