from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from src.application.use_cases.patient_auth import GetCurrentPatientUseCase
from src.integration.renovatio import RenovatioClient


@dataclass(frozen=True)
class PatientBalanceDto:
    balance: float
    patient_funds: float
    bonus_funds: float
    patient_debt: float
    patient_debt_company: float
    current_discount: float | None
    progress: float | None


@dataclass(frozen=True)
class ServiceCategoryDto:
    id: str
    title: str
    services_count: int
    children: list["ServiceCategoryDto"]


@dataclass(frozen=True)
class ServiceDto:
    service_id: str
    title: str
    code: str | None
    price: float | None
    category_id: str | None
    category_title: str | None
    category_path: str | None


@dataclass(frozen=True)
class AppointmentSlotDto:
    schedule_id: str
    doctor_id: str | None
    doctor_name: str
    profession: str | None
    clinic_id: str | None
    clinic_name: str | None
    room: str | None
    date: str
    time_start: str
    time_end: str | None
    service_id: str | None


class ServicesCatalogCache:
    def __init__(self, ttl_seconds: int = 43200) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._categories: list[ServiceCategoryDto] = []
        self._services: list[ServiceDto] = []
        self._updated_at: datetime | None = None

    def get(self) -> tuple[list[ServiceCategoryDto], list[ServiceDto]] | None:
        if not self._updated_at:
            return None
        if datetime.utcnow() - self._updated_at > self._ttl:
            return None
        return self._categories, self._services

    def set(self, categories: list[ServiceCategoryDto], services: list[ServiceDto]) -> None:
        self._categories = categories
        self._services = services
        self._updated_at = datetime.utcnow()


class PatientPortalDataUseCase:
    def __init__(self, sessions: GetCurrentPatientUseCase, renovatio_client: RenovatioClient, services_cache: ServicesCatalogCache | None = None) -> None:
        self._sessions = sessions
        self._client = renovatio_client
        self._services_cache = services_cache or ServicesCatalogCache()

    def get_balance(self, session_id: str) -> PatientBalanceDto:
        session = self._sessions.execute(session_id)
        raw = self._client.get_patient_balance(patient_id=session.patient_number)
        return PatientBalanceDto(
            balance=float(raw.get("balance") or 0),
            patient_funds=float(raw.get("patient_funds") or 0),
            bonus_funds=float(raw.get("bonus_funds") or 0),
            patient_debt=float(raw.get("patient_debt") or 0),
            patient_debt_company=float(raw.get("patient_debt_company") or 0),
            current_discount=_to_float(raw.get("current_discount")),
            progress=_to_float(raw.get("progress")),
        )

    def get_services_categories(self) -> list[ServiceCategoryDto]:
        categories, _ = self._load_services()
        return categories

    def get_services(self, category_id: str | None = None) -> list[ServiceDto]:
        _, services = self._load_services()
        if not category_id:
            return services
        return [item for item in services if item.category_id == category_id]

    def search_services(self, q: str, category_id: str | None = None) -> list[ServiceDto]:
        tokens = [token for token in q.lower().split() if token]
        items = self.get_services(category_id=category_id)
        if not tokens:
            return items
        return [item for item in items if all(token in item.title.lower() for token in tokens)]

    def get_schedule(self, session_id: str) -> list[AppointmentSlotDto]:
        session = self._sessions.execute(session_id)
        raw = self._client.get_schedule(patient_id=session.patient_number)
        slots: list[AppointmentSlotDto] = []
        for item in raw:
            slots.append(
                AppointmentSlotDto(
                    schedule_id=str(item.get("schedule_id") or item.get("id") or ""),
                    doctor_id=_to_str(item.get("doctor_id")),
                    doctor_name=str(item.get("doctor_name") or item.get("doctor") or "Специалист"),
                    profession=_to_str(item.get("profession") or item.get("specialization")),
                    clinic_id=_to_str(item.get("clinic_id")),
                    clinic_name=_to_str(item.get("clinic_name")),
                    room=_to_str(item.get("room")),
                    date=str(item.get("date") or ""),
                    time_start=str(item.get("time_start") or item.get("time") or ""),
                    time_end=_to_str(item.get("time_end")),
                    service_id=_to_str(item.get("service_id")),
                )
            )
        return slots

    def _load_services(self) -> tuple[list[ServiceCategoryDto], list[ServiceDto]]:
        cached = self._services_cache.get()
        if cached is not None:
            return cached
        raw_categories = self._client.get_service_categories()
        raw_services = self._client.get_services()
        categories = [
            ServiceCategoryDto(
                id=str(item.get("id") or item.get("category_id") or ""),
                title=str(item.get("title") or item.get("name") or "Категория"),
                services_count=int(item.get("services_count") or 0),
                children=[],
            )
            for item in raw_categories
        ]
        services = [
            ServiceDto(
                service_id=str(item.get("service_id") or item.get("id") or ""),
                title=str(item.get("title") or item.get("name") or "Услуга"),
                code=_to_str(item.get("code")),
                price=_to_float(item.get("price")),
                category_id=_to_str(item.get("category_id")),
                category_title=_to_str(item.get("category_title")),
                category_path=_to_str(item.get("category_path")),
            )
            for item in raw_services
        ]
        if any(c.services_count == 0 for c in categories):
            counts: dict[str, int] = {}
            for service in services:
                if service.category_id:
                    counts[service.category_id] = counts.get(service.category_id, 0) + 1
            categories = [ServiceCategoryDto(id=c.id, title=c.title, services_count=counts.get(c.id, c.services_count), children=c.children) for c in categories]
        self._services_cache.set(categories, services)
        return categories, services


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
