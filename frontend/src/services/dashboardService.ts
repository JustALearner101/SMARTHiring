import { API_ENDPOINTS } from "@/constants";
import { request, buildQuery } from "./base";

// ── Types ──────────────────────────────────────────────────────────────────

export interface MetricCard {
  key: string;
  label: string;
  value: number;
  change_percent: number;
  trend: "up" | "down" | "neutral";
}

export interface PipelineStage {
  status: string;
  label: string;
  count: number;
  color: string;
}

export interface TrendPoint {
  week_label: string;
  count: number;
}

export interface DashboardSummary {
  metrics: MetricCard[];
  pipeline: PipelineStage[];
  weekly_trend: TrendPoint[];
}

export interface UpcomingInterview {
  id: string;
  candidate_name: string;
  candidate_code: string;
  position: string;
  interviewer_name: string;
  interviewer_dept: string;
  scheduled_at: string;
  formatted_time: string;
  location_type: string;
  event_type: string;
  status: string;
}

export interface PendingApproval {
  id: string;
  candidate_name: string;
  position: string;
  proposed_slot: string;
  items_count: number;
  created_at: string;
  is_high_impact: boolean;
}

export interface ActiveNegotiation {
  id: string;
  candidate_name: string;
  position: string;
  channel: "whatsapp" | "email";
  current_round: number;
  max_rounds: number;
  last_message_preview: string;
  last_activity_at: string;
  status: string;
}

export interface RecentAudit {
  id: string;
  timestamp: string;
  event_type: string;
  title: string;
  actor: string;
  badge_variant: "success" | "warning" | "error" | "info";
}

export interface ActivityFeed {
  pending_approvals: PendingApproval[];
  active_negotiations: ActiveNegotiation[];
  recent_audit: RecentAudit[];
}

// ── API Methods ────────────────────────────────────────────────────────────

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>(API_ENDPOINTS.DASHBOARD_SUMMARY);
}

export async function fetchUpcomingInterviews(
  limit: number = 5
): Promise<UpcomingInterview[]> {
  const qs = buildQuery({ limit });
  return request<UpcomingInterview[]>(
    `${API_ENDPOINTS.DASHBOARD_UPCOMING_INTERVIEWS}${qs}`
  );
}

export async function fetchActivityFeed(): Promise<ActivityFeed> {
  return request<ActivityFeed>(API_ENDPOINTS.DASHBOARD_ACTIVITY_FEED);
}

