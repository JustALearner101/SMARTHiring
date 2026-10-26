/**
 * Application-wide constants and route definitions.
 */
export const API_ENDPOINTS = {
  HEALTH: "/health",

  // Authentication & Users
  AUTH_LOGIN: "/auth/login",
  AUTH_ME: "/auth/me",
  AUTH_USERS: "/auth/users",

  // Master data
  CANDIDATES: "/candidates",
  CONTACTS: "/contacts",
  HOLIDAYS: "/holidays",
  OPERATIONAL_RULES: "/operationalRules",
  RUBRICS: "/rubrics",

  // Orchestration
  ORCHESTRATOR_SCENARIOS: "/orchestrator/scenarios",
  ORCHESTRATOR_COMMAND: "/orchestrator/command",
  ACTION_PLANS: "/actionPlans",
  ACTION_PLANS_CURRENT: "/actionPlans/current",
  NEGOTIATION_THREADS: "/negotiationThreads",
  CALENDAR_MATRIX_EVENTS: "/calendarMatrix/events",
  SLOT_CONFLICT_CHECK: "/slotConflictChecker/check",

  // Simulator
  SIMULATOR_EMAIL_INBOX: "/simulator/email/inbox",
  SIMULATOR_WA_MESSAGES: "/simulator/whatsapp/messages",
  SIMULATOR_WA_SEND: "/simulator/whatsapp/send",
  SIMULATOR_WA_PRESETS: "/simulator/whatsapp/quickPresets",
  SIMULATOR_WA_NOTIFS: "/simulator/whatsapp/notifications",

  // Interviews
  INTERVIEW_SESSIONS: "/interviews/sessions",
  INTERVIEW_SESSIONS_UPLOAD: "/interviews/sessions/upload",
  INTERVIEW_TRANSCRIPTS: "/interviews/transcripts",
  INTERVIEW_DECISIONS: "/interviews/decisions",

  // Audit
  AUDIT_LOGS: "/auditLogs",
} as const;
