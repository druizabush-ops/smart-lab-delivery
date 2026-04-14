import { ApiClient } from "./client";

export type PatientDocument = { title: string; url: string | null; readiness: string };
export type PatientResult = {
  result_id: string;
  patient_id: string;
  status: string;
  channel: string;
  created_at: string;
  updated_at: string;
  attempts_count: number;
  last_error: string | null;
  documents: PatientDocument[];
};

export class ResultsApi {
  constructor(private readonly client: ApiClient) {}

  list(patientId: string): Promise<PatientResult[]> {
    return this.client.get<PatientResult[]>(`/patient/results?patient_id=${encodeURIComponent(patientId)}`);
  }

  get(resultId: string, patientId: string): Promise<PatientResult> {
    return this.client.get<PatientResult>(
      `/patient/results/${encodeURIComponent(resultId)}?patient_id=${encodeURIComponent(patientId)}`,
    );
  }
}
