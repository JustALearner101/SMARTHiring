/**
 * Orchestration & Accountability Domain Types (Milestone 3)
 * Maps to backend PostgreSQL models (tblm_action_plan, tblm_action_item, tblm_audit_log)
 * Adheres to the 5 Pillars of Agent Accountability (Sources, Permissions, Approval, Limits, Record)
 */

export type PlanStatus =
  | "IDLE"
  | "ANALYZING"
  | "CLARIFICATION_NEEDED"
  | "PENDING_APPROVAL"
  | "UNDO_WINDOW"
  | "EXECUTED"
  | "UNDONE"
  | "REJECTED";

export interface SourceCitation {
  id: string;
  ref_code: string; // e.g. "[cal-budi-01]", "[rule-jumatan]"
  source_type: "CALENDAR" | "OPERATIONAL_RULE" | "CANDIDATE_ATS" | "CONTACT";
  title: string;
  detail: string;
}

export interface ActionItemDraft {
  id: string;
  action_type: "send_email" | "send_whatsapp" | "book_calendar";
  recipient_name: string;
  recipient_role: string;
  recipient_contact: string;
  channel: "email" | "whatsapp" | "calendar";
  subject?: string;
  content_preview: string;
  is_external: boolean; // True for candidate WhatsApp (triggers High-Impact flag)
}

export interface ProposedSlot {
  title: string;
  start_utc: string;
  end_utc: string;
  formatted_wib: string;
  formatted_wita: string;
  duration_minutes: number;
  location_type: "Google Meet" | "Tencent Meeting" | "On-Site Room";
  meeting_link: string;
}

export interface ActionPlan {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_position: string;
  interviewer_id: string;
  interviewer_name: string;
  interviewer_role: string;
  interviewer_dept: string;
  raw_command: string;
  negotiation_round: number; // 1 to 3
  max_rounds: number;
  status: PlanStatus;
  is_high_impact: boolean;
  guardrail_passed: boolean;
  guardrail_notes: string;
  secondary_validator_passed: boolean;
  validator_notes: string;
  proposed_slot: ProposedSlot;
  sources_cited: SourceCitation[];
  items: ActionItemDraft[];
  created_at: string;
  undo_expires_at?: number; // Epoch timestamp for 60s countdown
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event_type:
  | "REQUEST_RECEIVED"
  | "GUARDRAIL_PASSED"
  | "DISAMBIGUATION_TRIGGERED"
  | "DISAMBIGUATION_RESOLVED"
  | "SOURCES_RETRIEVED"
  | "PLAN_VALIDATED"
  | "HUMAN_APPROVED"
  | "UNDO_BUFFER_STARTED"
  | "ACTION_UNDONE"
  | "ACTION_DISPATCHED";
  title: string;
  description: string;
  actor: string; // "AI Orchestrator" | "HR Admin (You)" | "Secondary Validator" | "Guardrail Scanner"
  status_badge: "success" | "warning" | "error" | "info";
  metadata?: Record<string, unknown>;
}

export interface DisambiguationProfile {
  id: string;
  name: string;
  employee_id: string;
  role: string;
  department: string;
  timezone: string;
  email: string;
  phone: string;
  working_hours: string;
  avatar_initials: string;
  notes: string;
}

export interface PresetScenario {
  id: string;
  label: string;
  tag: string;
  prompt: string;
  description: string;
}
