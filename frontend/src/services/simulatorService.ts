import { API_ENDPOINTS } from "@/constants";
import { buildQuery, request } from "./base";
import type {
  QuickReplyPreset,
  SimulatedEmail,
  SimulatedWhatsAppMessage,
  SimulatorNotification,
} from "@/types/simulator";

export async function listSimulatedEmails(
  folder: "inbox" | "sent" | "starred" = "inbox"
): Promise<SimulatedEmail[]> {
  const qs = buildQuery({ folder });
  return request<SimulatedEmail[]>(`${API_ENDPOINTS.SIMULATOR_EMAIL_INBOX}${qs}`);
}

export async function listWhatsAppMessages(
  threadId?: string
): Promise<SimulatedWhatsAppMessage[]> {
  const qs = buildQuery({ thread_id: threadId });
  return request<SimulatedWhatsAppMessage[]>(
    `${API_ENDPOINTS.SIMULATOR_WA_MESSAGES}${qs}`
  );
}

export interface SendWhatsAppInput {
  thread_id?: string;
  text: string;
  sender?: "candidate" | "interviewer" | "bot" | "system";
}

/** FastAPI declares thread_id/text/sender as Query(...) parameters. */
export async function sendWhatsAppMessage(
  input: SendWhatsAppInput
): Promise<SimulatedWhatsAppMessage> {
  const qs = buildQuery({
    thread_id: input.thread_id ?? "th-001",
    text: input.text,
    sender: input.sender ?? "candidate",
  });
  return request<SimulatedWhatsAppMessage>(
    `${API_ENDPOINTS.SIMULATOR_WA_SEND}${qs}`,
    { method: "POST" }
  );
}

export async function listQuickPresets(): Promise<QuickReplyPreset[]> {
  return request<QuickReplyPreset[]>(API_ENDPOINTS.SIMULATOR_WA_PRESETS);
}

export async function listSimulatorNotifications(): Promise<SimulatorNotification[]> {
  return request<SimulatorNotification[]>(API_ENDPOINTS.SIMULATOR_WA_NOTIFS);
}
