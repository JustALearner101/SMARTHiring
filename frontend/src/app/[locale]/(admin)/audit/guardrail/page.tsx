import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Guardrail & Injection Alerts | SmartHiring Orchestrator",
  description: "Prompt injection detection, embedded instruction quarantine, and security alerts",
};

export default function GuardrailAlertsPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Guardrail & Injection Alerts" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Prompt Injection & Security Guardrails
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Monitoring pertahanan keamanan AI terhadap serangan *prompt injection* pada CV pelamar, dokumen meeting, dan balasan chat.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-error-50 px-3 py-1 text-xs font-medium text-error-600 dark:bg-error-500/15 dark:text-error-400">
            Security Scanner
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error-50 text-error-500 dark:bg-error-500/10">
            🚨
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Quarantined Instructions & Security Flags
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Daftar flag instruksi tertanam (`tblt_flag.vflag_type = EMBEDDED_INSTRUCTION`) yang berhasil diblokir sebelum masuk ke model perencana (Planner).
          </p>
        </div>
      </div>
    </div>
  );
}
