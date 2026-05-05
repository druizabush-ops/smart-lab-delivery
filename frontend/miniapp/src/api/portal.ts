import { ApiClient } from "./client";

export type LoyaltyDto = {
  balance: number;
  patient_funds: number;
  bonus_funds: number;
  patient_debt: number;
  patient_debt_company: number;
  current_discount?: number | null;
  progress?: number | null;
};

export type ServiceCategoryDto = { id: string; title: string; services_count: number };
export type ServiceDto = { service_id: string; title: string; price?: number | null; category_id?: string | null };
export type AppointmentSlotDto = {
  schedule_id: string;
  doctor_name: string;
  profession?: string | null;
  clinic_name?: string | null;
  room?: string | null;
  date: string;
  time_start: string;
};

export class PortalApi {
  constructor(private readonly client: ApiClient) {}
  loyalty(): Promise<LoyaltyDto> { return this.client.get("/patient/loyalty"); }
  serviceCategories(): Promise<ServiceCategoryDto[]> { return this.client.get("/patient/services/categories"); }
  services(categoryId?: string): Promise<ServiceDto[]> {
    const query = categoryId ? `?category_id=${encodeURIComponent(categoryId)}` : "";
    return this.client.get(`/patient/services${query}`);
  }
  searchServices(q: string, categoryId?: string): Promise<ServiceDto[]> {
    const params = new URLSearchParams({ q });
    if (categoryId) params.set("category_id", categoryId);
    return this.client.get(`/patient/services/search?${params.toString()}`);
  }
  schedule(): Promise<AppointmentSlotDto[]> { return this.client.get("/patient/appointments/schedule"); }
}
