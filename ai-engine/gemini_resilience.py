"""Clasificación compartida de errores del proveedor Gemini."""

import httpx
from google.genai import errors


RETRYABLE_STATUS_CODES = {408, 500, 502, 503, 504}


class GeminiQuotaError(RuntimeError):
    """Límite de solicitudes o cuota de Gemini."""


class GeminiTransientError(RuntimeError):
    """Error temporal de Gemini o de conexión."""


class GeminiPermanentError(RuntimeError):
    """Error no recuperable mediante un reintento inmediato."""


def classify_gemini_error(error: Exception) -> RuntimeError:
    """Clasifica errores usando tipos y códigos del SDK."""

    if isinstance(error, errors.APIError):
        code = error.code

        if code == 429:
            return GeminiQuotaError(
                "Gemini alcanzó un límite de solicitudes o cuota."
            )

        if code in RETRYABLE_STATUS_CODES:
            return GeminiTransientError(
                f"Gemini devolvió un error temporal HTTP {code}."
            )

        return GeminiPermanentError(
            f"Gemini devolvió un error HTTP {code}."
        )

    if isinstance(error, (httpx.TimeoutException, httpx.TransportError)):
        return GeminiTransientError(
            "Error temporal de conexión con Gemini."
        )

    return GeminiPermanentError(
        "Error inesperado al consultar Gemini."
    )


def generate_content_safely(client, model: str, prompt: str):
    """Genera contenido y normaliza los errores del SDK."""
    try:
        return client.models.generate_content(
            model=model,
            contents=prompt,
        )
    except Exception as error:
        classified = classify_gemini_error(error)
        raise classified from error
