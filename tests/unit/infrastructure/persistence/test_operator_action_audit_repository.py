from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories import OperatorActionAuditRepository


def test_operator_action_audit_repository_persists_event() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    repository = OperatorActionAuditRepository(session_factory=factory)

    repository.save(
        command="requeue",
        card_id="card-1",
        success=True,
        message="ok",
        reason="manual",
        actor="operator-1",
        source="ui",
    )

    with factory() as session:
        row = session.execute(text("SELECT command, card_id, success, actor FROM operator_action_log")).one()
        assert row[0] == "requeue"
        assert row[1] == "card-1"
        assert row[2] == 1
        assert row[3] == "operator-1"
