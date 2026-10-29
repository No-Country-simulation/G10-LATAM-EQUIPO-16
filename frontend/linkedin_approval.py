"""Contrato de aprobación LinkedIn para la interfaz Aigoraweave.

No realiza autenticación, peticiones HTTP ni publicaciones.
La autorización efectiva corresponde exclusivamente a Spring Boot.
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


MAX_CONTENT_LENGTH = 3000
VALID_STATUSES = frozenset({"PENDING", "CONFIRMED"})


@dataclass(frozen=True)
class LinkedInApprovalView:
    approval_id: str
    content: str
    content_sha256: str
    expires_at: datetime
    status: str


def validate_content(content: str) -> str:
    """Valida el texto final sin modificar su contenido."""

    if not isinstance(content, str):
        raise ValueError("El contenido debe ser texto.")

    if not content.strip():
        raise ValueError("El contenido no puede estar vacío.")

    if len(content) > MAX_CONTENT_LENGTH:
        raise ValueError("El contenido supera el límite permitido.")

    return content


def parse_approval_response(data: dict[str, Any]) -> LinkedInApprovalView:
    """Valida una respuesta del backend sin otorgar permisos."""

    if not isinstance(data, dict):
        raise ValueError("Respuesta de aprobación inválida.")

    approval_id = data.get("approvalId")
    content = validate_content(data.get("content"))
    content_sha256 = data.get("contentSha256")
    expires_at = data.get("expiresAt")
    status = data.get("status")

    if not isinstance(approval_id, str) or not approval_id.strip():
        raise ValueError("Identificador de aprobación inválido.")

    if (
        not isinstance(content_sha256, str)
        or len(content_sha256) != 64
        or any(c not in "0123456789abcdef" for c in content_sha256)
    ):
        raise ValueError("Hash de aprobación inválido.")

    actual_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    if not hmac.compare_digest(actual_hash, content_sha256):
        raise ValueError("El contenido no coincide con su hash.")

    if status not in VALID_STATUSES:
        raise ValueError("Estado de aprobación inválido.")

    if not isinstance(expires_at, str):
        raise ValueError("Expiración de aprobación inválida.")

    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Expiración de aprobación inválida.") from exc

    if expiry.tzinfo is None:
        raise ValueError("La expiración debe incluir zona horaria.")

    if expiry <= datetime.now(timezone.utc):
        raise ValueError("La aprobación ha expirado.")

    return LinkedInApprovalView(
        approval_id=approval_id,
        content=content,
        content_sha256=content_sha256,
        expires_at=expiry,
        status=status,
    )
