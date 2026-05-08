from src.application.use_cases.bot_patient import BotMiniAppTokenUseCase, BotProfileCipher, InMemoryBotPatientProfileRepository


def test_cipher_roundtrip() -> None:
    cipher = BotProfileCipher("secret-key")
    encrypted = cipher.encrypt("pass123")
    assert encrypted != "pass123"
    assert cipher.decrypt(encrypted) == "pass123"


def test_miniapp_token_one_time_redeem() -> None:
    repo = InMemoryBotPatientProfileRepository()
    use_case = BotMiniAppTokenUseCase(repo, ttl_minutes=5)
    token = use_case.create("max-user-1")
    assert use_case.redeem(token) == "max-user-1"
    assert use_case.redeem(token) is None
