import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Rubrics & Competencies | SmartHiring Orchestrator",
  description: "Interview round profiles and evaluation competency rubrics",
};

export default function RubricsPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Rubrics & Competencies" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Evaluation Rubrics & Competency Profiles
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Profil ronde wawancara (`tblm_profile`) dan daftar parameter penilaian kompetensi berbobot (`tblm_competency`).
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            Assessment Config
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            📊
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Rubrics & Competencies Manager
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Konfigurasi indikator kompetensi (misal: Leadership, System Design, Communication) dan klasifikasi visibilitas akses per peran.
          </p>
        </div>
      </div>
    </div>
  );
}
