export type UserRole = "HR" | "USER_INTERVIEWER" | "TECH_INTERVIEWER" | "AUDITOR";

export interface UserProfile {
  id: string;
  employee_id: string;
  name: string;
  username: string;
  email: string;
  role: UserRole;
  department?: string | null;
  position?: string | null;
  timezone?: string;
  working_hours?: string | null;
  status?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
