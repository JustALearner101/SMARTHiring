/**
 * SmartHiring (Heketon) — Master Data API Contract
 * Represents ground truth reference entities for AI retriever and operational policies.
 * Aligns with backend Pydantic DTOs and PostgreSQL schema (tblm_*).
 */

export type Timezone = "WIB" | "WITA" | "WIT";

export type PreferredChannel = "whatsapp" | "email";

export type ApplicationStatus =
  | "SCREENING"
  | "ESCALATED"
  | "INTERVIEW_SCHEDULED"
  | "COMPLETED"
  | "OFFERED"
  | "REJECTED";

export interface Candidate {
  id: string;
  candidate_code: string;
  name: string;
  email: string;
  phone: string;
  preferred_channel: PreferredChannel;
  applied_position: string;
  status: ApplicationStatus;
  timezone: Timezone;
  resume_url?: string;
  notes?: string;
  created_at: string;
}

export type CandidateCreateInput = Omit<Candidate, "id" | "candidate_code" | "created_at">;
export type CandidateUpdateInput = Partial<CandidateCreateInput>;

export type Department =
  | "Engineering"
  | "Product"
  | "Finance"
  | "People Operations"
  | "Operations";

export interface InterviewerContact {
  id: string;
  employee_id: string;
  name: string;
  email: string;
  phone: string;
  department: Department;
  role: string;
  timezone: Timezone;
  working_hours: string;
  avatar_initials: string;
}

export type InterviewerCreateInput = Omit<InterviewerContact, "id" | "avatar_initials">;
export type InterviewerUpdateInput = Partial<InterviewerCreateInput>;

export interface OperationalPolicy {
  work_start_time: string; // "09:00"
  work_end_time: string;   // "17:00"
  friday_prayer_start: string; // "11:30"
  friday_prayer_end: string;   // "13:00"
  max_negotiation_rounds: number; // default: 3
  buffer_minutes: number; // default: 15
  injection_guardrail_enabled: boolean;
}

export interface NationalHoliday {
  id: string;
  date: string; // "YYYY-MM-DD"
  name: string;
  is_joint_leave: boolean; // Cuti bersama flag
}

export type NationalHolidayCreateInput = Omit<NationalHoliday, "id">;

export interface CompetencyItem {
  id: string;
  code: string;
  name: string;
  description: string;
  weight: number; // percentage (e.g. 25)
  target_score: number; // 1 to 5
}

export interface RubricProfile {
  id: string;
  code: string;
  round_name: string;
  description: string;
  competencies: CompetencyItem[];
}

/**
 * Standard API Response envelope matching backend ApiResponse[T]
 */
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
