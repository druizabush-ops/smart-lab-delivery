"""Единая точка вычисления операционного id карточки доставки."""

from src.domain.entities import DeliveryCard


def build_operational_card_id(card: DeliveryCard) -> str:
    """Возвращает deterministic id карточки для runtime queue/repository."""

    return f"{card.patient_id}:{card.lab_result_id}"
