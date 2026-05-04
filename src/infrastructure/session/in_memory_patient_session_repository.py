"""In-memory repository для patient server-side sessions."""

from src.application.use_cases.patient_auth import PatientSession


class InMemoryPatientSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, PatientSession] = {}

    def save(self, session: PatientSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> PatientSession | None:
        return self._sessions.get(session_id)

    def deactivate(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        self._sessions[session_id] = PatientSession(
            session_id=session.session_id,
            patient_key=session.patient_key,
            patient_name=session.patient_name,
            patient_number=session.patient_number,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_refresh_at=session.last_refresh_at,
            auth_type=session.auth_type,
            birth_date=session.birth_date,
            phone=session.phone,
            email=session.email,
            avatar_url=session.avatar_url,
            is_active=False,
        )
