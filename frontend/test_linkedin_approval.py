"""Pruebas del contrato de aprobación de LinkedIn."""

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from frontend.linkedin_approval import (
    MAX_CONTENT_LENGTH,
    parse_approval_response,
    validate_content,
)


def approval_response(content="Publicación de prueba", minutes=10):
    return {
        "approvalId": "approval-test-123",
        "content": content,
        "contentSha256": hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
        "expiresAt": (
            datetime.now(timezone.utc) + timedelta(minutes=minutes)
        ).isoformat(),
        "status": "PENDING",
    }


def test_valid_content_preserves_text():
    content = "  Publicación de prueba  "
    assert validate_content(content) == content


def test_empty_content_rejected():
    for content in ("", "   ", "\n\t"):
        with pytest.raises(ValueError):
            validate_content(content)


def test_content_over_limit_rejected():
    with pytest.raises(ValueError):
        validate_content("A" * (MAX_CONTENT_LENGTH + 1))


def test_valid_backend_response():
    data = approval_response()
    result = parse_approval_response(data)

    assert result.approval_id == data["approvalId"]
    assert result.content == data["content"]
    assert result.status == "PENDING"
    assert result.expires_at.tzinfo is not None


def test_invalid_hash_format_rejected():
    data = approval_response()
    data["contentSha256"] = "invalid"

    with pytest.raises(ValueError):
        parse_approval_response(data)


def test_expired_approval_rejected():
    data = approval_response(minutes=-1)

    with pytest.raises(ValueError):
        parse_approval_response(data)


def test_modified_content_rejected():
    data = approval_response()
    data["content"] = "Contenido modificado"

    with pytest.raises(ValueError, match="hash"):
        parse_approval_response(data)
