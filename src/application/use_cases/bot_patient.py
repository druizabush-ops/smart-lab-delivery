"""Use cases для MAX patient bot profile/auto-login."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.application.use_cases.patient_auth import PatientLoginUseCase


@dataclass
class BotPatientProfile:
    max_user_id: str
    patient_login: str | None = None
    encrypted_patient_password: str | None = None
    last_success_login_at: datetime | None = None


@dataclass
class BotLoginToken:
    max_user_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None


class InMemoryBotPatientProfileRepository:
    def __init__(self) -> None:
        self._profiles: dict[str, BotPatientProfile] = {}
        self._tokens: dict[str, BotLoginToken] = {}

    def get(self, max_user_id: str) -> BotPatientProfile | None:
        return self._profiles.get(max_user_id)

    def save(self, profile: BotPatientProfile) -> None:
        self._profiles[profile.max_user_id] = profile

    def delete(self, max_user_id: str) -> None:
        self._profiles.pop(max_user_id, None)

    def save_token(self, token_hash: str, token: BotLoginToken) -> None:
        self._tokens[token_hash] = token

    def get_token(self, token_hash: str) -> BotLoginToken | None:
        return self._tokens.get(token_hash)


class BotProfileCipher:
    def __init__(self, key: str) -> None:
        if not key.strip():
            raise ValueError("BOT_PROFILE_ENCRYPTION_KEY is required")
        self._key = key.encode("utf-8")

    def encrypt(self, plaintext: str) -> str:
        nonce = secrets.token_bytes(16)
        payload = plaintext.encode("utf-8")
        stream = self._stream(nonce, len(payload))
        encrypted = bytes(a ^ b for a, b in zip(payload, stream, strict=True))
        blob = nonce + encrypted
        return base64.urlsafe_b64encode(blob).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        blob = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
        nonce, encrypted = blob[:16], blob[16:]
        stream = self._stream(nonce, len(encrypted))
        payload = bytes(a ^ b for a, b in zip(encrypted, stream, strict=True))
        return payload.decode("utf-8")

    def _stream(self, nonce: bytes, size: int) -> bytes:
        output = b""
        counter = 0
        while len(output) < size:
            block = hmac.new(self._key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
            output += block
            counter += 1
        return output[:size]


class BotProfileUseCase:
    def __init__(self, repository: InMemoryBotPatientProfileRepository, cipher: BotProfileCipher) -> None:
        self._repository = repository
        self._cipher = cipher

    def save_login(self, max_user_id: str, login: str) -> None:
        profile = self._repository.get(max_user_id) or BotPatientProfile(max_user_id=max_user_id)
        profile.patient_login = login
        self._repository.save(profile)

    def save_password(self, max_user_id: str, password: str) -> None:
        profile = self._repository.get(max_user_id) or BotPatientProfile(max_user_id=max_user_id)
        profile.encrypted_patient_password = self._cipher.encrypt(password)
        self._repository.save(profile)

    def delete_profile(self, max_user_id: str) -> None:
        self._repository.delete(max_user_id)

    def has_credentials(self, max_user_id: str) -> bool:
        profile = self._repository.get(max_user_id)
        return bool(profile and profile.patient_login and profile.encrypted_patient_password)

    def get_credentials(self, max_user_id: str) -> tuple[str, str]:
        profile = self._repository.get(max_user_id)
        if not profile or not profile.patient_login or not profile.encrypted_patient_password:
            raise ValueError("Профиль не заполнен")
        return profile.patient_login, self._cipher.decrypt(profile.encrypted_patient_password)


class BotCheckLoginUseCase:
    def __init__(self, profiles: BotProfileUseCase, patient_login_use_case: PatientLoginUseCase, repository: InMemoryBotPatientProfileRepository) -> None:
        self._profiles = profiles
        self._patient_login_use_case = patient_login_use_case
        self._repository = repository

    def execute(self, max_user_id: str) -> bool:
        login, password = self._profiles.get_credentials(max_user_id)
        try:
            self._patient_login_use_case.execute(login, password)
        except Exception:
            return False
        profile = self._repository.get(max_user_id)
        if profile:
            profile.last_success_login_at = datetime.now(tz=timezone.utc)
            self._repository.save(profile)
        return True


class BotMiniAppTokenUseCase:
    def __init__(self, repository: InMemoryBotPatientProfileRepository, *, ttl_minutes: int = 5) -> None:
        self._repository = repository
        self._ttl = ttl_minutes

    def create(self, max_user_id: str) -> str:
        token = secrets.token_urlsafe(24)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self._repository.save_token(
            token_hash,
            BotLoginToken(max_user_id=max_user_id, token_hash=token_hash, expires_at=datetime.now(tz=timezone.utc) + timedelta(minutes=self._ttl)),
        )
        return token

    def redeem(self, token: str) -> str | None:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        saved = self._repository.get_token(token_hash)
        if not saved:
            return None
        now = datetime.now(tz=timezone.utc)
        if saved.used_at is not None or saved.expires_at <= now:
            return None
        saved.used_at = now
        return saved.max_user_id


def build_bot_cipher_from_env() -> BotProfileCipher:
    return BotProfileCipher(os.getenv("BOT_PROFILE_ENCRYPTION_KEY", ""))
