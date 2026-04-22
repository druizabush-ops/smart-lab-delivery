import { ApiClient } from "./client";

export type PatientResultListItem = {
  result_id: string;
  title: string;
  date: string | null;
  status: string;
  has_pdf: boolean;
  lab_name: string | null;
  clinic_name: string | null;
  short_services_summary: string | null;
};

export type PatientResultDetails = {
  result_id: string;
  title: string;
  date: string | null;
  status: string;
  has_pdf: boolean;
  lab_name: string | null;
  clinic_name: string | null;
  services: string[];
  sections: Array<Record<string, unknown>>;
  indicators: Array<Record<string, unknown>>;
  pdf_open_url: string | null;
  pdf_download_url: string | null;
};

export class ResultsApi {
  constructor(private readonly client: ApiClient) {}

  list(): Promise<PatientResultListItem[]> {
    return this.client.get<PatientResultListItem[]>("/patient/results");
  }

  get(resultId: string): Promise<PatientResultDetails> {
    return this.client.get<PatientResultDetails>(`/patient/results/${encodeURIComponent(resultId)}`);
  }
}
