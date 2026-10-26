import { API_ENDPOINTS } from "@/constants";
import { buildQuery, request } from "./base";
import type { AuditEvent } from "@/types/orchestration";
import type { PaginatedResponse } from "@/types/master";

export interface AuditLogParams {
  page?: number;
  page_size?: number;
}

export async function listAuditLogs(
  params: AuditLogParams = {}
): Promise<PaginatedResponse<AuditEvent>> {
  const qs = buildQuery({ page: params.page, page_size: params.page_size });
  return request<PaginatedResponse<AuditEvent>>(`${API_ENDPOINTS.AUDIT_LOGS}${qs}`);
}
