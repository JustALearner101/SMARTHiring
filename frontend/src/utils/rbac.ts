import type { UserRole } from "@/types/auth";

/**
 * Normalizes legacy stored role strings so existing localStorage sessions
 * migrate cleanly to the 3-role RBAC model (HR, ADMIN, INTERVIEWER).
 */
export function normalizeUserRole(
  rawRole: string | null | undefined
): UserRole | null {
  if (!rawRole) return null;
  const upper = rawRole.trim().toUpperCase();
  if (upper === "HR") return "HR";
  if (upper === "ADMIN" || upper === "AUDITOR") return "ADMIN";
  if (
    upper === "INTERVIEWER" ||
    upper === "USER_INTERVIEWER" ||
    upper === "TECH_INTERVIEWER"
  ) {
    return "INTERVIEWER";
  }
  return null;
}

/**
 * Client-side route access matrix aligned with backend `require_roles(...)`:
 * - ADMIN: Full access to ALL modules and pages.
 * - HR: Dashboard, AI Orchestrator, Interviews & Copilot, Master Data (all 4), Simulator (no /audit/*).
 * - INTERVIEWER: Dashboard, Calendar Matrix (/orchestration/calendar), Interviews & Copilot (/interviews/*),
 *   Master Data ONLY Evaluation Rubrics (/master/rubrics), and Email Simulator (/simulator/email).
 */
export function isRouteAllowedForRole(
  pathname: string,
  role: UserRole | null
): boolean {
  if (!role) return false;

  // Per explicit governance requirement: ADMIN has full access to all pages
  if (role === "ADMIN") return true;

  const cleanPath = pathname.trim() || "/";

  if (role === "HR") {
    return !cleanPath.startsWith("/audit");
  }

  if (role === "INTERVIEWER") {
    if (cleanPath === "/") return true;
    if (cleanPath.startsWith("/orchestration/calendar")) return true;
    if (cleanPath.startsWith("/interviews")) return true;
    if (cleanPath.startsWith("/master/rubrics")) return true;
    if (cleanPath.startsWith("/simulator/email")) return true;
    return false;
  }

  return false;
}

