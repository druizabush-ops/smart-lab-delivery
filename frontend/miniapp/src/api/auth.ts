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

export type PhoneAuthPending = {
  patient_id: string;
  phone: string;
  need_auth_key: boolean;
};

export class AuthApi {
  constructor(private readonly client: ApiClient) {}

  login(login: string, password: string): Promise<PatientSession> {
    return this.client.post<PatientSession>("/patient/auth/login", { login, password });
  }

  loginByPhone(phone: string): Promise<PhoneAuthPending> {
    return this.client.post<PhoneAuthPending>("/patient/auth/phone", { phone });
  }

  confirmCode(patientId: string, code: string): Promise<PatientSession> {
    return this.client.post<PatientSession>("/patient/auth/confirm-code", { patient_id: patientId, code });
  }

  me(): Promise<PatientSession> {
    return this.client.get<PatientSession>("/patient/auth/me");
  }

  logout(): Promise<{ success: boolean }> {
    return this.client.post<{ success: boolean }>("/patient/auth/logout");
  }
}
