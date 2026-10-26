import { API_ENDPOINTS } from "@/constants";
import { buildQuery, jsonPost, request } from "./base";
import type {
  HrDecision,
  HrDecisionType,
  InterviewSession,
  InterviewUploadRequest,
  TranscriptSegment,
} from "@/types/interview";
import type { PaginatedResponse } from "@/types/master";

export interface InterviewListParams {
  candidate_code?: string;
  page?: number;
  page_size?: number;
}

export async function listInterviewSessions(
  params: InterviewListParams = {}
): Promise<PaginatedResponse<InterviewSession>> {
  const qs = buildQuery({
    candidate_code: params.candidate_code,
    page: params.page,
    page_size: params.page_size,
  });
  return request<PaginatedResponse<InterviewSession>>(
    `${API_ENDPOINTS.INTERVIEW_SESSIONS}${qs}`
  );
}

export async function getInterviewSession(
  interviewId: string
): Promise<InterviewSession> {
  return request<InterviewSession>(
    `${API_ENDPOINTS.INTERVIEW_SESSIONS}/${encodeURIComponent(interviewId)}`
  );
}

export async function uploadInterviewSession(
  input: InterviewUploadRequest
): Promise<InterviewSession> {
  return request<InterviewSession>(
    API_ENDPOINTS.INTERVIEW_SESSIONS_UPLOAD,
    jsonPost(input)
  );
}

export async function getInterviewTranscripts(
  interviewId: string
): Promise<TranscriptSegment[]> {
  return request<TranscriptSegment[]>(
    `${API_ENDPOINTS.INTERVIEW_TRANSCRIPTS}/${encodeURIComponent(interviewId)}`
  );
}

export interface HrDecisionInput {
  decision: HrDecisionType;
  notes: string;
  decided_by?: string;
}

export async function saveHrDecision(
  interviewId: string,
  input: HrDecisionInput
): Promise<HrDecision> {
  return request<HrDecision>(
    `${API_ENDPOINTS.INTERVIEW_DECISIONS}/${encodeURIComponent(interviewId)}`,
    jsonPost({
      decision: input.decision,
      notes: input.notes,
      decided_by: input.decided_by ?? "HR Admin",
    })
  );
}
