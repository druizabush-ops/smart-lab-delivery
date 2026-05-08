from datetime import datetime

from pydantic import BaseModel, Field


class PatientLoginRequest(BaseModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)


class PatientPhoneLoginRequest(BaseModel):
    phone: str = Field(min_length=5)


class ConfirmPatientCodeRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    code: str = Field(min_length=1)


class PatientSessionResponse(BaseModel):
    session_id: str
    patient_name: str
    patient_number: str
    created_at: datetime
    expires_at: datetime
    last_refresh_at: datetime
    auth_type: str


class PhoneAuthPendingResponse(BaseModel):
    patient_id: str
    phone: str
    need_auth_key: bool


class LogoutResponse(BaseModel):
    success: bool
