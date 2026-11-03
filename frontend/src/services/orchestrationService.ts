import { API_ENDPOINTS } from "@/constants";
import {
  buildQuery,
  isNotFoundError,
  jsonPost,
  request,
} from "./base";
import type {
  ActionItemDraft,
  ActionPlan,
  CalendarMatrixEvent,
  DisambiguationProfile,
  NegotiationThread,
  PresetScenario,
  SlotConflictCheckRequest,
  SlotConflictCheckResult,
  ThreadMessage,
} from "@/types/orchestration";
import type { PaginatedResponse } from "@/types/master";

export interface DisambiguationResult {
  status: "CLARIFICATION_NEEDED";
  message: string;
  profiles: DisambiguationProfile[];
}

export interface OutOfScopeResult {
  status: "OUT_OF_SCOPE_REFUSED";
  escalation_reason: string;
  human_owner?: string;
  message: string;
}

export interface DeadlockEscalatedResult {
  status: "DEADLOCK_ESCALATED";
  escalation_reason: string;
  message: string;
}

export interface GuardrailBlockedResult {
  status: "GUARDRAIL_BLOCKED";
  message: string;
  guardrail_notes?: string;
}

export type OrchestratorCommandResult =
  | ActionPlan
  | DisambiguationResult
  | OutOfScopeResult
  | DeadlockEscalatedResult
  | GuardrailBlockedResult;

export function isDisambiguationResult(
  result: OrchestratorCommandResult
): result is DisambiguationResult {
  return (
    (result as DisambiguationResult)?.status === "CLARIFICATION_NEEDED" &&
    Array.isArray((result as DisambiguationResult)?.profiles)
  );
}

export function isOutOfScopeResult(
  result: OrchestratorCommandResult
): result is OutOfScopeResult {
  return (result as OutOfScopeResult)?.status === "OUT_OF_SCOPE_REFUSED";
}

export function isDeadlockResult(
  result: OrchestratorCommandResult
): result is DeadlockEscalatedResult {
  return (result as DeadlockEscalatedResult)?.status === "DEADLOCK_ESCALATED";
}

export function isGuardrailBlockedResult(
  result: OrchestratorCommandResult
): result is GuardrailBlockedResult {
  return (result as GuardrailBlockedResult)?.status === "GUARDRAIL_BLOCKED";
}

/**
 * Backend returns undo_expires_at as Unix seconds (int(time.time() + 60)),
 * while the UI countdown works in milliseconds.
 */
function normalizePlan(plan: ActionPlan): ActionPlan {
  if (plan.undo_expires_at && plan.undo_expires_at < 1e12) {
    return { ...plan, undo_expires_at: plan.undo_expires_at * 1000 };
  }
  return plan;
}

export interface CommandInput {
  command: string;
  scenario_id?: string | null;
}

export async function listPresetScenarios(): Promise<PresetScenario[]> {
  return request<PresetScenario[]>(API_ENDPOINTS.ORCHESTRATOR_SCENARIOS);
}

export async function executeCommand(
  input: CommandInput
): Promise<OrchestratorCommandResult> {
  const result = await request<OrchestratorCommandResult>(
    API_ENDPOINTS.ORCHESTRATOR_COMMAND,
    jsonPost(input)
  );
  if (
    isDisambiguationResult(result) ||
    isOutOfScopeResult(result) ||
    isDeadlockResult(result) ||
    isGuardrailBlockedResult(result)
  ) {
    return result;
  }
  return normalizePlan(result as ActionPlan);
}

/** Returns null when the backend has no active plan (HTTP 404 or inactive). */
export async function getCurrentActionPlan(): Promise<ActionPlan | null> {
  try {
    const plan = await request<ActionPlan>(API_ENDPOINTS.ACTION_PLANS_CURRENT);
    return normalizePlan(plan);
  } catch (error) {
    if (isNotFoundError(error)) return null;
    console.warn("No active action plan currently available:", error);
    return null;
  }
}

/** Fetches a specific ActionPlan by ID (HTTP 404 or invalid returns null). */
export async function getActionPlan(planId: string): Promise<ActionPlan | null> {
  const cleanId = String(planId || "").trim();
  if (!cleanId || cleanId === "undefined" || cleanId === "null") {
    return null;
  }
  try {
    const plan = await request<ActionPlan>(
      `${API_ENDPOINTS.ACTION_PLANS}/${encodeURIComponent(cleanId)}`
    );
    return normalizePlan(plan);
  } catch (error) {
    if (isNotFoundError(error)) return null;
    console.warn("Action plan not found or unavailable:", cleanId, error);
    return null;
  }
}

export interface ApprovalInput {
  approved_by?: string;
  send_immediately?: boolean;
  customized_items?: ActionItemDraft[];
}

export async function approveActionPlan(
  planId: string,
  input: ApprovalInput = {}
): Promise<ActionPlan> {
  const plan = await request<ActionPlan>(
    `${API_ENDPOINTS.ACTION_PLANS}/${encodeURIComponent(planId)}/approve`,
    jsonPost({
      approved_by: input.approved_by ?? "HR Admin (You)",
      send_immediately: input.send_immediately ?? false,
      customized_items: input.customized_items,
    })
  );
  return normalizePlan(plan);
}

export async function undoActionPlan(
  planId: string,
  reason = "Manual cancellation by HR within 60s window"
): Promise<ActionPlan> {
  const plan = await request<ActionPlan>(
    `${API_ENDPOINTS.ACTION_PLANS}/${encodeURIComponent(planId)}/undo`,
    jsonPost({ reason })
  );
  return normalizePlan(plan);
}

export async function rejectActionPlan(
  planId: string,
  reason = "Plan rejected by HR at approval gate"
): Promise<ActionPlan> {
  const plan = await request<ActionPlan>(
    `${API_ENDPOINTS.ACTION_PLANS}/${encodeURIComponent(planId)}/reject`,
    jsonPost({ reason, rejected_by: "HR Admin (You)" })
  );
  return normalizePlan(plan);
}

export interface ThreadListParams {
  status?: string;
  page?: number;
  page_size?: number;
}

export async function listNegotiationThreads(
  params: ThreadListParams = {}
): Promise<PaginatedResponse<NegotiationThread>> {
  const qs = buildQuery({
    status: params.status,
    page: params.page,
    page_size: params.page_size,
  });
  return request<PaginatedResponse<NegotiationThread>>(
    `${API_ENDPOINTS.NEGOTIATION_THREADS}${qs}`
  );
}

export async function getNegotiationThread(
  threadId: string
): Promise<NegotiationThread> {
  return request<NegotiationThread>(
    `${API_ENDPOINTS.NEGOTIATION_THREADS}/${encodeURIComponent(threadId)}`
  );
}

export interface ThreadReplyInput {
  content: string;
  sender_role?: string;
  channel?: string;
}

/** FastAPI declares these as Query(...) parameters, not a JSON body. */
export async function replyNegotiationThread(
  threadId: string,
  input: ThreadReplyInput
): Promise<ThreadMessage> {
  const qs = buildQuery({
    content: input.content,
    sender_role: input.sender_role ?? "HR_ADMIN",
    channel: input.channel ?? "whatsapp",
  });
  return request<ThreadMessage>(
    `${API_ENDPOINTS.NEGOTIATION_THREADS}/${encodeURIComponent(threadId)}/reply${qs}`,
    { method: "POST" }
  );
}

export interface CalendarEventParams {
  user_id?: string;
  start?: string;
  end?: string;
}

export async function listCalendarEvents(
  params: CalendarEventParams = {}
): Promise<CalendarMatrixEvent[]> {
  const qs = buildQuery({
    user_id: params.user_id,
    start: params.start,
    end: params.end,
  });
  return request<CalendarMatrixEvent[]>(
    `${API_ENDPOINTS.CALENDAR_MATRIX_EVENTS}${qs}`
  );
}

export async function checkSlotConflict(
  input: SlotConflictCheckRequest
): Promise<SlotConflictCheckResult> {
  return request<SlotConflictCheckResult>(
    API_ENDPOINTS.SLOT_CONFLICT_CHECK,
    jsonPost(input)
  );
}
