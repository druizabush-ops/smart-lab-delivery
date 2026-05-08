import { ApiClient } from "./client";

export type PatientSession = {
  session_id: string;
  patient_name: string;
  patient_number: string;
  created_at: string;
  expires_at: string;
  last_refresh_at: string;
  auth_type: "login" | "phone";
};

export class AuthApi {
  constructor(private readonly client: ApiClient) {}

  login(login: string, password: string): Promise<PatientSession> {
    return this.client.post<PatientSession>("/patient/auth/login", { login, password });
  }

  me(): Promise<PatientSession> {
    return this.client.get<PatientSession>("/patient/auth/me");
  }

  autoLoginByToken(autoLoginToken: string): Promise<PatientSession> {
    return this.client.post<PatientSession>("/patient/auth/auto-login-token", { auto_login_token: autoLoginToken });
  }

  logout(): Promise<{ success: boolean }> {
    return this.client.post<{ success: boolean }>("/patient/auth/logout");
  }

  unbind(): Promise<{ success: boolean }> {
    return this.client.post<{ success: boolean }>("/patient/auth/unbind");
  }
}
