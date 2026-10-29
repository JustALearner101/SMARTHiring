import { API_ENDPOINTS } from "@/constants";
import { request } from "./base";

export interface SystemNotification {
  id: string;
  category: "APPROVAL" | "SECURITY" | "TRIAGE" | "INTERVIEW";
  title: string;
  message: string;
  timestamp: string;
  link: string;
  badge_variant: "error" | "warning" | "success" | "info";
  isRead?: boolean;
  metadata?: Record<string, unknown> | null;
}

export const notificationService = {
  async getNotifications(): Promise<SystemNotification[]> {
    const data = await request<SystemNotification[]>(API_ENDPOINTS.NOTIFICATIONS);
    return data || [];
  },
};
