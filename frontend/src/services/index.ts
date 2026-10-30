/**
 * API service modules for communicating with the FastAPI backend.
 */
export * as masterService from "./masterService";
export * as orchestrationService from "./orchestrationService";
export * as dashboardService from "./dashboardService";
export * as simulatorService from "./simulatorService";
export * as interviewService from "./interviewService";
export * as auditService from "./auditService";
export { authService } from "./authService";
export {
  notificationService,
  type SystemNotification,
} from "./notificationService";
export * from "./base";