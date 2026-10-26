import { API_ENDPOINTS } from "@/constants";
import type { LoginRequest, LoginResponse, UserProfile } from "@/types/auth";
import { jsonPost, request } from "./base";

export const authService = {
  /**
   * Authenticate system user and receive JWT access token.
   */
  async login(payload: LoginRequest): Promise<LoginResponse> {
    return request<LoginResponse>(API_ENDPOINTS.AUTH_LOGIN, jsonPost(payload));
  },

  /**
   * Get currently authenticated user profile.
   */
  async getMe(): Promise<UserProfile> {
    return request<UserProfile>(API_ENDPOINTS.AUTH_ME);
  },

  /**
   * List available demo users (HR, Interviewer, Auditor) for rapid role switching.
   */
  async listDemoUsers(): Promise<UserProfile[]> {
    return request<UserProfile[]>(API_ENDPOINTS.AUTH_USERS);
  },
};
