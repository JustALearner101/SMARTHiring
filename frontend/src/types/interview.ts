/**
 * Types for Interview Assessment & Copilot Module (Milestone 5)
 * Adheres to relational schema (tblt_interview, tblt_transcript_segment, tblt_summary_point, tblt_summary_evidence, tblt_hr_decision)
 * Follows Hackathon Rulebook Challenge B: Consent check, 100% evidence citation, and two-tier Interviewer -> HR decision handoff
 */

import type { ApplicationStatus } from "./master";

export type ConsentStatus = "GRANTED" | "NOT_GRANTED" | "WITHDRAWN";

export type InterviewScopeFilter = "mine" | "awaiting_hr" | "all";

export type JobStatus =
  | "RECEIVED"
  | "ACCESS_CHECKED"
  | "TRANSCRIBED"
  | "SUMMARIZED"
  | "AUDITED"
  | "IN_REVIEW"
  | "COMPLETED"
  | "REJECTED_NO_CONSENT";

export type HrDecisionType = "ADVANCE" | "HOLD" | "REJECT";
export type AdvanceNextStage = "NEXT_INTERVIEW" | "TECHNICAL_TEST" | "OFFERED";
export type DecisionActorRole = "INTERVIEWER" | "HR";
export type DecisionWorkflowStatus = "PENDING_HR_FOLLOWUP" | "FINALIZED";

export interface TranscriptSegment {
  id: string;
  segment_no: number;
  start_ms: number;
  end_ms: number;
  timestamp_formatted: string;
  speaker_label: string;
  speaker_type: "CANDIDATE" | "INTERVIEWER" | "UNKNOWN";
  speaker_name: string;
  text: string;
  confidence: number;
  is_uncertain: boolean;
}

export interface SummaryEvidence {
  id: string;
  transcript_segment_id: string;
  quote_text: string;
  timestamp_formatted: string;
  start_ms: number;
  relevance_score: number;
}

export interface CompetencySummaryPoint {
  id: string;
  competency_code: string;
  competency_name: string;
  coverage_status: "COVERED" | "PARTIAL" | "NOT_DISCUSSED";
  content: string;
  verification_status: "VERIFIED" | "UNVERIFIED" | "NOT_APPLICABLE";
  evidences: SummaryEvidence[];
}

export interface HrDecision {
  decision: HrDecisionType;
  next_stage?: AdvanceNextStage | null;
  resulting_candidate_status?: ApplicationStatus | null;
  actor_role?: DecisionActorRole;
  workflow_status?: DecisionWorkflowStatus;
  notes: string;
  decided_at: string;
  decided_by: string;
  decided_by_user_id?: string | null;
}

export interface InterviewUploadRequest {
  candidate_id: string;
  profile_id: string;
  interviewer_id?: string | null;
  consent_status?: ConsentStatus;
  audio_url?: string;
  audio_duration?: string;
  notes?: string;
}

export interface InterviewSession {
  id: string;
  candidate_id: string;
  profile_id?: string | null;
  interviewer_id?: string | null;
  candidate_name: string;
  candidate_code: string;
  position: string;
  round_name: string;
  interviewer_name: string;
  interviewer_role: string;
  scheduled_at: string;
  consent_status: ConsentStatus;
  consent_at?: string;
  consent_notice_version?: string;
  audio_url?: string;
  audio_duration?: string;
  job_status: JobStatus;
  progress_percentage?: number;
  current_step?: string;
  asr_engine?: string;
  competency_points?: CompetencySummaryPoint[];
  hr_decision?: HrDecision;
}
