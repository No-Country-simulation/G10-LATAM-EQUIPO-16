import httpx
import pytest
from google.genai import errors

from gemini_resilience import (
    GeminiPermanentError,
    GeminiQuotaError,
    GeminiTransientError,
    classify_gemini_error,
)


@pytest.mark.parametrize("code", [408, 500, 502, 503, 504])
def test_retryable_http_codes(code):
    error = errors.ServerError(
        code=code,
        response_json={"error": {"message": "Temporal"}},
    )

    assert isinstance(
        classify_gemini_error(error),
        GeminiTransientError,
    )


def test_quota_error():
    error = errors.ClientError(
        code=429,
        response_json={"error": {"message": "Quota exceeded"}},
    )

    assert isinstance(
        classify_gemini_error(error),
        GeminiQuotaError,
    )


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_permanent_http_codes(code):
    error = errors.ClientError(
        code=code,
        response_json={"error": {"message": "Invalid request"}},
    )

    assert isinstance(
        classify_gemini_error(error),
        GeminiPermanentError,
    )


def test_timeout_is_transient():
    error = httpx.ReadTimeout("Request timed out")

    assert isinstance(
        classify_gemini_error(error),
        GeminiTransientError,
    )


def test_unexpected_error_is_permanent():
    assert isinstance(
        classify_gemini_error(ValueError("Unexpected")),
        GeminiPermanentError,
    )
