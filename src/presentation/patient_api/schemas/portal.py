from pydantic import BaseModel


class PatientBalanceResponse(BaseModel):
    balance: float
    patient_funds: float
    bonus_funds: float
    patient_debt: float
    patient_debt_company: float
    current_discount: float | None = None
    progress: float | None = None


class ServiceCategoryResponse(BaseModel):
    id: str
    title: str
    services_count: int
    children: list["ServiceCategoryResponse"] = []


class ServiceResponse(BaseModel):
    service_id: str
    title: str
    code: str | None = None
    price: float | None = None
    category_id: str | None = None
    category_title: str | None = None
    category_path: str | None = None


class AppointmentSlotResponse(BaseModel):
    schedule_id: str
    doctor_id: str | None = None
    doctor_name: str
    profession: str | None = None
    clinic_id: str | None = None
    clinic_name: str | None = None
    room: str | None = None
    date: str
    time_start: str
    time_end: str | None = None
    service_id: str | None = None
