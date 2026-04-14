import hashlib
import hmac
from urllib.parse import urlencode

from src.application.security.max_webapp_validation import validate_max_webapp_data


def _build_signed_init_data(secret: str) -> str:
    fields = {
        "query_id": "abc",
        "user": '{"id":"patient-001"}',
        "start_param": "result:card-1",
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", secret.encode("utf-8"), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_validate_max_webapp_data_accepts_valid_signature() -> None:
    init_data = _build_signed_init_data("test-secret")

    result = validate_max_webapp_data(init_data, "test-secret")

    assert result.is_valid is True
    assert result.user_id == "patient-001"


def test_validate_max_webapp_data_rejects_invalid_signature() -> None:
    init_data = _build_signed_init_data("test-secret")

    result = validate_max_webapp_data(init_data, "wrong-secret")

    assert result.is_valid is False
    assert "подпись" in (result.reason or "")
