import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Candidate WhatsApp Simulator | SmartHiring Orchestrator",
  description: "Interactive WhatsApp chat simulator for candidates to test interview invitations, rejections, and rescheduling",
};

export default function CandidateWhatsappSimulatorPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Candidate WhatsApp Simulator" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Candidate WhatsApp Chat Simulator
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Simulasi obrolan WhatsApp kandidat untuk menguji pengiriman pesan undangan ramah dan simulasi balasan penolakan / usul jadwal baru.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-success-50 px-3 py-1 text-xs font-medium text-success-600 dark:bg-success-500/15 dark:text-success-400">
            High-Impact Channel
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-success-50 text-success-500 dark:bg-success-500/10">
            📱
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Simulated WhatsApp Chat Interface
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Ketik balasan kandidat (cth: &quot;Maaf kak tanggal 25 ada sidang. Kalau tanggal 26 jam 2 siang bisa?&quot;) untuk menguji logika deteksi bentrok jadwal dan aturan ibadah.
          </p>
        </div>
      </div>
    </div>
  );
}
