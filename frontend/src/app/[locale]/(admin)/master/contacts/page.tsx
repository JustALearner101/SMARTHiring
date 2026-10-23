import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Interviewer Directory | SmartHiring Orchestrator",
  description: "Internal contacts, hiring managers, and interviewer profiles",
};

export default function ContactsPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Interviewer Directory" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Interviewer & Internal Contact Directory
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Direktori karyawan / Hiring Manager (`tblm_user` / `contacts`), role departemen, email, dan zona waktu domisili.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
            Disambiguation Ready
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-500/10">
            📇
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Internal Contacts Table (Termasuk Kasus Uji Dua Pak Budi)
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Tabel kontak yang siap menguji skenario disambiguasi nama kembar panitia hackathon (misal: Budi Santoso - Engineering WIB vs Budi Raharjo - Finance WITA).
          </p>
        </div>
      </div>
    </div>
  );
}
