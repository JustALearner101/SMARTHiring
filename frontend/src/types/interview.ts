/**
 * Types for Interview Assessment & Copilot Module (Milestone 5)
 * Adheres to relational schema (tblt_interview, tblt_transcript_segment, tblt_summary_point, tblt_summary_evidence, tblt_hr_decision)
 * Follows Hackathon Rulebook Challenge B: Consent check, 100% evidence citation, and HR decision gate
 */

export type ConsentStatus = "GRANTED" | "NOT_GRANTED" | "WITHDRAWN";

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

export interface TranscriptSegment {
  id: string;
  segment_no: number;
  start_ms: number;
  end_ms: number;
  timestamp_formatted: string; // e.g. "12:45"
  speaker_label: string; // e.g. "SPEAKER_1"
  speaker_type: "CANDIDATE" | "INTERVIEWER" | "UNKNOWN";
  speaker_name: string; // "Budi Santoso" | "Rina Kusuma"
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
  competency_code: string; // e.g. "C1", "C2"
  competency_name: string; // e.g. "System Architecture & Scalability"
  coverage_status: "COVERED" | "PARTIAL" | "NOT_DISCUSSED";
  content: string; // Neutral, descriptive summary without biased rating (BR-01)
  verification_status: "VERIFIED" | "UNVERIFIED" | "NOT_APPLICABLE";
  evidences: SummaryEvidence[];
}

export interface HrDecision {
  decision: HrDecisionType;
  notes: string;
  decided_at: string;
  decided_by: string;
}

export interface InterviewSession {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_code: string; // Pseudonym code e.g. "K-014" (per SDD D-03)
  position: string;
  round_name: string; // e.g. "User Technical Interview (Round 1)"
  interviewer_name: string;
  interviewer_role: string;
  scheduled_at: string;
  consent_status: ConsentStatus;
  consent_at?: string;
  consent_notice_version?: string;
  audio_url?: string;
  audio_duration?: string; // e.g. "45:20"
  job_status: JobStatus;
  competency_points?: CompetencySummaryPoint[];
  hr_decision?: HrDecision;
}
