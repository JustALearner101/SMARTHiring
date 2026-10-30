import { API_ENDPOINTS } from "@/constants";
import { buildQuery, request } from "./base";
import type { AuditEvent } from "@/types/orchestration";
import type { PaginatedResponse } from "@/types/master";

export interface AuditLogParams {
  page?: number;
  page_size?: number;
}

export interface AuditStats {
  total_events: number;
  total_system_logs: number;
  total_system_errors: number;
  hash_chain_valid: boolean;
  latest_event_timestamp: string | null;
}

export interface HashChainVerification {
  is_valid: boolean;
  total_blocks: number;
  genesis_hash: string;
  latest_hash: string;
  algorithm: string;
  broken_at_block_id?: number | null;
  verified_at: string;
}

export interface SystemLog {
  nid: number;
  vlog_level: "INFO" | "WARN" | "ERROR";
  vlog_message: string;
  vlog_stacktrace?: string | null;
  vlog_source?: string | null;
  vlog_path?: string | null;
  vlog_method?: string | null;
  vlog_status_code?: string | null;
  dcrea: string;
}

export interface SystemLogParams {
  page?: number;
  page_size?: number;
  level?: string;
  source?: string;
  search?: string;
}

export async function listAuditLogs(
  params: AuditLogParams = {}
): Promise<PaginatedResponse<AuditEvent>> {
  const qs = buildQuery({ page: params.page, page_size: params.page_size });
  return request<PaginatedResponse<AuditEvent>>(`${API_ENDPOINTS.AUDIT_LOGS}${qs}`);
}

export async function getAuditStats(): Promise<AuditStats> {
  return request<AuditStats>(API_ENDPOINTS.AUDIT_STATS);
}

export async function verifyHashChain(): Promise<HashChainVerification> {
  return request<HashChainVerification>(API_ENDPOINTS.AUDIT_VERIFY);
}

export async function listSystemLogs(
  params: SystemLogParams = {}
): Promise<PaginatedResponse<SystemLog>> {
  const qs = buildQuery({
    page: params.page,
    page_size: params.page_size,
    level: params.level,
    source: params.source,
    search: params.search,
  });
  return request<PaginatedResponse<SystemLog>>(`${API_ENDPOINTS.SYSTEM_LOGS}${qs}`);
}
