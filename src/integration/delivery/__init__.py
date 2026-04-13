"""Адаптеры отправки в каналы доставки."""

from .email_provider import EmailDeliveryProvider
from .max_provider import MaxDeliveryProvider

__all__ = ["EmailDeliveryProvider", "MaxDeliveryProvider"]
