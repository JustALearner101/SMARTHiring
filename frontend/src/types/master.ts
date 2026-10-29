/**
 * SmartHiring (Heketon) — Master Data API Contract
 * Represents ground truth reference entities for AI retriever and operational policies.
 * Aligns with backend Pydantic DTOs and PostgreSQL schema (tblm_*).
 */

import type { UserRole } from "./auth";

export type Timezone = "WIB" | "WITA" | "WIT";

export type PreferredChannel = "whatsapp" | "email";

export type ApplicationStatus =
  | "SCREENING"
  | "ESCALATED"
  | "INTERVIEW_SCHEDULED"
  | "PENDING_HR_REVIEW"
  | "TECHNICAL_TEST"
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
  current_salary?: number | null;
  expected_salary?: number | null;
  application_cycle?: number;
  previous_application_id?: string | null;
  created_at: string;
}

export type CandidateCreateInput = Omit<
  Candidate,
  | "id"
  | "candidate_code"
  | "status"
  | "created_at"
  | "application_cycle"
  | "previous_application_id"
> & {
  status?: ApplicationStatus;
};
export type CandidateUpdateInput = Partial<CandidateCreateInput>;

export type Department =
  | "Engineering"
  | "Product"
  | "Finance"
  | "People Operations"
  | "Human Resources"
  | "Internal Audit"
  | "Operations"
  | string;

export interface InterviewerContact {
  id: string;
  employee_id: string;
  name: string;
  username?: string;
  email: string;
  phone: string;
  department: Department;
  role: string;
  system_role?: UserRole;
  timezone: Timezone;
  working_hours: string;
  avatar_initials: string;
}

export interface InterviewerCreateInput {
  employee_id: string;
  name: string;
  username: string;
  password: string;
  email: string;
  phone: string;
  department: Department;
  role: string;
  system_role: UserRole;
  timezone: Timezone;
  working_hours: string;
}

export interface InterviewerUpdateInput {
  employee_id?: string;
  name?: string;
  username?: string;
  password?: string;
  email?: string;
  phone?: string;
  department?: Department;
  role?: string;
  system_role?: UserRole;
  timezone?: Timezone;
  working_hours?: string;
}

export interface OperationalPolicy {
  work_start_time: string;
  work_end_time: string;
  friday_prayer_start: string;
  friday_prayer_end: string;
  max_negotiation_rounds: number;
  buffer_minutes: number;
  injection_guardrail_enabled: boolean;
}

export interface NationalHoliday {
  id: string;
  date: string;
  name: string;
  is_joint_leave: boolean;
}

export type NationalHolidayCreateInput = Omit<NationalHoliday, "id">;

export type RubricTargetRole = "HR" | "INTERVIEWER";

export interface CompetencyItem {
  id: string;
  code: string;
  name: string;
  description: string;
  weight: number;
  target_score: number;
}

export interface CompetencyCreateInput {
  code: string;
  name: string;
  description: string;
  weight?: number;
  target_score?: number;
}

export type CompetencyUpdateInput = Partial<CompetencyCreateInput>;

export interface RubricProfile {
  id: string;
  code: string;
  round_name: string;
  description: string;
  target_role?: RubricTargetRole;
  department?: string | null;
  owner_user_id?: string | null;
  owner_name?: string | null;
  competencies: CompetencyItem[];
}

export interface RubricProfileCreateInput {
  code: string;
  round_name: string;
  description?: string;
  target_role?: RubricTargetRole;
  department?: string;
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
  total_pages?: number;
  has_next?: boolean;
  has_prev?: boolean;
}
