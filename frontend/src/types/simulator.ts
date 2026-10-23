/**
 * Types for Dual-Mode Communication Simulator (Milestone 4)
 * Supports WhatsApp chat simulator and Interviewer Email webmail simulator
 * Synchronized with AI Orchestrator Triage Loop and Guardrail Scanner
 */

export type SimulatorChannel = "email" | "whatsapp";

export type MessageSenderRole = "candidate" | "interviewer" | "bot" | "system";

export type DeliveryStatus = "sending" | "sent" | "delivered" | "read";

export interface SimulatedEmail {
  id: string;
  thread_id: string;
  sender_name: string;
  sender_email: string;
  sender_role: string;
  recipient_name: string;
  recipient_email: string;
  subject: string;
  body_text: string;
  sent_at: string;
  is_read: boolean;
  is_starred: boolean;
  folder: "inbox" | "sent" | "starred";
  tags: Array<"Invitation" | "Reschedule" | "Confirmation" | "High-Impact">;
  meeting_details?: {
    platform: string;
    meeting_link: string;
    date_formatted: string;
    time_wib: string;
    time_wita: string;
    calendar_ref: string;
  };
}

export interface SimulatedWhatsAppMessage {
  id: string;
  thread_id: string;
  sender: MessageSenderRole;
  sender_name: string;
  text: string;
  timestamp: string;
  status: DeliveryStatus;
  is_guardrail_flagged?: boolean;
  guardrail_reason?: string;
  action_trigger?: "CONFIRM_SCHEDULE" | "REQUEST_RESCHEDULE" | "REJECT_INVITATION" | "SECURITY_ALERT";
  action_metadata?: {
    proposed_slot?: string;
    conflict_detected?: boolean;
    conflict_reason?: string;
  };
}

export type QuickPresetType = "confirm" | "reschedule" | "friday_conflict" | "prompt_injection";

export interface QuickReplyPreset {
  id: string;
  preset_type: QuickPresetType;
  label: string;
  badge: string;
  badge_variant: "success" | "warning" | "danger" | "info";
  description: string;
  payload_text: string;
}

export interface SimulatorNotification {
  id: string;
  type: "triage_triggered" | "guardrail_blocked" | "confirmed" | "scheduled";
  title: string;
  message: string;
  timestamp: string;
  action_url?: string;
}
