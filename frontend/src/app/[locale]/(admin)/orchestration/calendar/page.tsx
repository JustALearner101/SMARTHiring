import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Calendar Matrix | SmartHiring Orchestrator",
  description: "Cross-timezone interview calendar with operational rule blocks",
};

export default function CalendarMatrixPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Calendar Matrix" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Interviewer Calendar & Timezone Matrix
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Sinkronisasi kalender slot kosong dengan konversi WIB/WITA/WIT dan pemblokiran waktu Sholat Jumat.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-success-50 px-3 py-1 text-xs font-medium text-success-600 dark:bg-success-500/15 dark:text-success-400">
            Pilar: PERMISSIONS
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-success-50 text-success-500 dark:bg-success-500/10">
            📅
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Calendar View & Conflict Checker
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Matriks kalender ketersediaan interviewer, visualisasi bentrok jam kerja (09:00 - 17:00), dan blokir Sholat Jumat (11:30 - 13:00).
          </p>
        </div>
      </div>
    </div>
  );
}
