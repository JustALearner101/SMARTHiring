import { API_ENDPOINTS } from "@/constants";
import {
  buildQuery,
  jsonPatch,
  jsonPost,
  jsonPut,
  request,
} from "./base";
import type {
  Candidate,
  CandidateCreateInput,
  CandidateUpdateInput,
  InterviewerContact,
  InterviewerCreateInput,
  InterviewerUpdateInput,
  NationalHoliday,
  NationalHolidayCreateInput,
  OperationalPolicy,
  PaginatedResponse,
  RubricProfile,
} from "@/types/master";

export interface CandidateListParams {
  query?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function listCandidates(
  params: CandidateListParams = {}
): Promise<PaginatedResponse<Candidate>> {
  const qs = buildQuery({
    query: params.query,
    status: params.status,
    page: params.page,
    page_size: params.page_size,
  });
  return request<PaginatedResponse<Candidate>>(`${API_ENDPOINTS.CANDIDATES}${qs}`);
}

export async function getCandidate(candidateId: string): Promise<Candidate> {
  return request<Candidate>(`${API_ENDPOINTS.CANDIDATES}/${encodeURIComponent(candidateId)}`);
}

export async function createCandidate(
  input: CandidateCreateInput
): Promise<Candidate> {
  return request<Candidate>(API_ENDPOINTS.CANDIDATES, jsonPost(input));
}

export async function updateCandidate(
  candidateId: string,
  input: CandidateUpdateInput
): Promise<Candidate> {
  return request<Candidate>(
    `${API_ENDPOINTS.CANDIDATES}/${encodeURIComponent(candidateId)}`,
    jsonPatch(input)
  );
}

export async function listContacts(department?: string): Promise<InterviewerContact[]> {
  const qs = buildQuery({ department });
  return request<InterviewerContact[]>(`${API_ENDPOINTS.CONTACTS}${qs}`);
}

export async function createContact(
  input: InterviewerCreateInput
): Promise<InterviewerContact> {
  return request<InterviewerContact>(API_ENDPOINTS.CONTACTS, jsonPost(input));
}

export async function updateContact(
  userId: string,
  input: InterviewerUpdateInput
): Promise<InterviewerContact> {
  return request<InterviewerContact>(
    `${API_ENDPOINTS.CONTACTS}/${encodeURIComponent(userId)}`,
    jsonPatch(input)
  );
}

export async function getOperationalPolicy(): Promise<OperationalPolicy> {
  return request<OperationalPolicy>(API_ENDPOINTS.OPERATIONAL_RULES);
}

export async function updateOperationalPolicy(
  policy: OperationalPolicy
): Promise<OperationalPolicy> {
  return request<OperationalPolicy>(API_ENDPOINTS.OPERATIONAL_RULES, jsonPut(policy));
}

export async function listHolidays(year?: number): Promise<NationalHoliday[]> {
  const qs = buildQuery({ year });
  return request<NationalHoliday[]>(`${API_ENDPOINTS.HOLIDAYS}${qs}`);
}

export async function createHoliday(
  input: NationalHolidayCreateInput
): Promise<NationalHoliday> {
  return request<NationalHoliday>(API_ENDPOINTS.HOLIDAYS, jsonPost(input));
}

export async function listRubrics(): Promise<RubricProfile[]> {
  return request<RubricProfile[]>(API_ENDPOINTS.RUBRICS);
}
