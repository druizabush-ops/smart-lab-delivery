"""Use case регистрации результата попытки доставки."""

from src.domain.entities import DeliveryAttempt, DeliveryCard


class RegisterDeliveryResultUseCase:
    """Добавляет попытку в карточку и делегирует обновление статусов домену."""

    def execute(self, card: DeliveryCard, attempt: DeliveryAttempt) -> DeliveryCard:
        """Регистрирует попытку и возвращает обновленную карточку."""

        card.add_attempt(attempt)
        return card
