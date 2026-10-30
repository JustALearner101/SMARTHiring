import { API_ENDPOINTS } from "@/constants";
import { buildQuery, jsonDelete, jsonPost, request } from "./base";
import type {
  AdvanceNextStage,
  HrDecision,
  HrDecisionType,
  InterviewScopeFilter,
  InterviewSession,
  InterviewUploadRequest,
  TranscriptSegment,
} from "@/types/interview";
import type { PaginatedResponse } from "@/types/master";

export interface InterviewListParams {
  candidate_code?: string;
  scope?: InterviewScopeFilter;
  page?: number;
  page_size?: number;
}

export async function listInterviewSessions(
  params: InterviewListParams = {}
): Promise<PaginatedResponse<InterviewSession>> {
  const qs = buildQuery({
    candidate_code: params.candidate_code,
    scope: params.scope,
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

export async function getInterviewSessionStatus(
  interviewId: string
): Promise<InterviewSession> {
  return request<InterviewSession>(
    `${API_ENDPOINTS.INTERVIEW_SESSIONS}/${encodeURIComponent(interviewId)}/status`
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

export async function uploadInterviewFile(
  formData: FormData
): Promise<InterviewSession> {
  const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/interviews/sessions/upload-file`;
  const storedToken =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const storedRole =
    typeof window !== "undefined" ? localStorage.getItem("auth_role") : null;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      ...(storedToken ? { Authorization: `Bearer ${storedToken}` } : {}),
      ...(storedRole ? { "X-Demo-Role": storedRole } : {}),
    },
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      errorData.detail || errorData.message || `Upload failed with status: ${res.status}`
    );
  }
  const json = await res.json();
  return json.data;
}

export async function deleteInterviewSession(
  interviewId: string
): Promise<{ id: string }> {
  return request<{ id: string }>(
    `${API_ENDPOINTS.INTERVIEW_SESSIONS}/${encodeURIComponent(interviewId)}`,
    jsonDelete()
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
  next_stage?: AdvanceNextStage | null;
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
      next_stage: input.decision === "ADVANCE" ? (input.next_stage ?? "NEXT_INTERVIEW") : null,
      notes: input.notes,
      decided_by: input.decided_by,
    })
  );
}


export async function swapSessionSpeakers(
  interviewId: string
): Promise<InterviewSession> {
  return request<InterviewSession>(
    `${API_ENDPOINTS.INTERVIEW_TRANSCRIPTS}/${encodeURIComponent(interviewId)}/swap-speakers`,
    jsonPost({})
  );
}

export async function reEvaluateSession(
  interviewId: string
): Promise<InterviewSession> {
  return request<InterviewSession>(
    `${API_ENDPOINTS.INTERVIEW_TRANSCRIPTS}/${encodeURIComponent(interviewId)}/re-evaluate`,
    jsonPost({})
  );
}
