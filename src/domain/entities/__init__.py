"""Пакет доменных сущностей Smart Lab Delivery."""

from .channels import DeliveryChannel
from .delivery_attempt import DeliveryAttempt
from .delivery_card import DeliveryCard
from .lab_result import LabResult
from .patient import Patient

__all__ = [
    "DeliveryChannel",
    "DeliveryAttempt",
    "DeliveryCard",
    "LabResult",
    "Patient",
]
