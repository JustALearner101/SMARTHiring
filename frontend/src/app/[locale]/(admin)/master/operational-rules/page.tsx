import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Operational Rules | SmartHiring Orchestrator",
  description: "Work calendar rules, working hours, Friday prayer blocks, and national holidays",
};

export default function OperationalRulesPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Operational Rules" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Operational Rules & Work Calendar
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Aturan jam kerja Indonesia (09:00 - 17:00), blokir Sholat Jumat (11:30 - 13:00), dan kalender libur nasional (`tblm_holiday`).
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-error-50 px-3 py-1 text-xs font-medium text-error-600 dark:bg-error-500/15 dark:text-error-400">
            Pilar: PERMISSIONS
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error-50 text-error-500 dark:bg-error-500/10">
            ⚙️
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Operational Rules & Policy Settings
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Kelola batasan jam kerja harian, konversi zona waktu (WIB/WITA/WIT), daftar cuti bersama, dan batas maksimal putaran negosiasi (default 3 ronde).
          </p>
        </div>
      </div>
    </div>
  );
}
