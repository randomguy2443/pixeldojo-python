"""
Custom exceptions for PixelDojo API client.

Provides a clear exception hierarchy for handling different error scenarios:
- Authentication failures
- Insufficient credits
- Rate limiting
- General API errors
"""

from __future__ import annotations

from typing import Any


class PixelDojoError(Exception):
    """Base exception for all PixelDojo errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r})"
        )


class AuthenticationError(PixelDojoError):
    """Raised when API authentication fails (401 Unauthorized)."""

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=401, **kwargs)


class InsufficientCreditsError(PixelDojoError):
    """Raised when account has insufficient credits (402 Payment Required)."""

    def __init__(
        self,
        message: str = "Insufficient credits to complete this request",
        credits_remaining: float | None = None,
        credits_required: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=402, **kwargs)
        self.credits_remaining = credits_remaining
        self.credits_required = credits_required

    def __str__(self) -> str:
        base = super().__str__()
        if self.credits_remaining is not None:
            return f"{base} (remaining: {self.credits_remaining})"
        return base


class RateLimitError(PixelDojoError):
    """Raised when rate limit is exceeded (429 Too Many Requests)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base} (retry after {self.retry_after}s)"
        return base


class APIError(PixelDojoError):
    """Raised for general API errors (5xx, network issues, etc.)."""

    def __init__(
        self,
        message: str = "API request failed",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)


class ValidationError(PixelDojoError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Request validation failed",
        field: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=422, **kwargs)
        self.field = field


class TimeoutError(PixelDojoError):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.timeout = timeout


class ConnectionError(PixelDojoError):
    """Raised when connection to the API fails."""

    def __init__(
        self,
        message: str = "Failed to connect to PixelDojo API",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
