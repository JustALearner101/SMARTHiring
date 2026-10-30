import { API_ENDPOINTS } from "@/constants";
import {
  buildQuery,
  jsonDelete,
  jsonPatch,
  jsonPost,
  jsonPut,
  request,
  type QueryValue,
} from "./base";
import type {
  Candidate,
  CandidateCreateInput,
  CandidateUpdateInput,
  CompetencyCreateInput,
  CompetencyItem,
  CompetencyUpdateInput,
  InterviewerContact,
  InterviewerCreateInput,
  InterviewerUpdateInput,
  NationalHoliday,
  NationalHolidayCreateInput,
  OperationalPolicy,
  PaginatedResponse,
  RubricProfile,
  RubricProfileCreateInput,
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

export async function deleteCandidate(candidateId: string): Promise<{ id: string }> {
  return request<{ id: string }>(
    `${API_ENDPOINTS.CANDIDATES}/${encodeURIComponent(candidateId)}`,
    jsonDelete()
  );
}

export interface CandidateReapplyInput {
  applied_position?: string;
  notes?: string;
  expected_salary?: number;
}

export async function reapplyCandidate(
  candidateId: string,
  input: CandidateReapplyInput = {}
): Promise<Candidate> {
  return request<Candidate>(
    `${API_ENDPOINTS.CANDIDATES}/${encodeURIComponent(candidateId)}/reapply`,
    jsonPost(input)
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

export async function deleteContact(userId: string): Promise<{ id: string }> {
  return request<{ id: string }>(
    `${API_ENDPOINTS.CONTACTS}/${encodeURIComponent(userId)}`,
    jsonDelete()
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

export async function deleteHoliday(holidayId: string): Promise<{ id: string }> {
  return request<{ id: string }>(
    `${API_ENDPOINTS.HOLIDAYS}/${encodeURIComponent(holidayId)}`,
    jsonDelete()
  );
}

export interface RubricListFilter {
  forInterviewerId?: string;
  candidateId?: string;
}

export async function listRubrics(
  params?: string | RubricListFilter
): Promise<RubricProfile[]> {
  const queryObj: Record<string, QueryValue> = {};
  if (typeof params === "string") {
    queryObj.for_interviewer_id = params;
  } else if (params) {
    if (params.forInterviewerId) queryObj.for_interviewer_id = params.forInterviewerId;
    if (params.candidateId) queryObj.candidate_id = params.candidateId;
  }
  const qs = buildQuery(queryObj);
  return request<RubricProfile[]>(`${API_ENDPOINTS.RUBRICS}${qs}`);
}

export async function createRubricProfile(
  input: RubricProfileCreateInput
): Promise<RubricProfile> {
  return request<RubricProfile>(API_ENDPOINTS.RUBRICS, jsonPost(input));
}

export async function deleteRubricProfile(profileId: string): Promise<{ id: string }> {
  return request<{ id: string }>(
    `${API_ENDPOINTS.RUBRICS}/${encodeURIComponent(profileId)}`,
    jsonDelete()
  );
}

export async function reEvaluateRubric(profileId: string): Promise<RubricProfile> {
  return request<RubricProfile>(
    `${API_ENDPOINTS.RUBRICS}/${encodeURIComponent(profileId)}/re-evaluate`,
    jsonPost({})
  );
}

export async function createCompetency(
  profileId: string,
  input: CompetencyCreateInput
): Promise<CompetencyItem> {
  return request<CompetencyItem>(
    `${API_ENDPOINTS.RUBRICS}/${encodeURIComponent(profileId)}/competencies`,
    jsonPost(input)
  );
}

export async function updateCompetency(
  profileId: string,
  competencyId: string,
  input: CompetencyUpdateInput
): Promise<CompetencyItem> {
  return request<CompetencyItem>(
    `${API_ENDPOINTS.RUBRICS}/${encodeURIComponent(profileId)}/competencies/${encodeURIComponent(competencyId)}`,
    jsonPatch(input)
  );
}

export async function deleteCompetency(
  profileId: string,
  competencyId: string
): Promise<{ id: string }> {
  return request<{ id: string }>(
    `${API_ENDPOINTS.RUBRICS}/${encodeURIComponent(profileId)}/competencies/${encodeURIComponent(competencyId)}`,
    jsonDelete()
  );
}
