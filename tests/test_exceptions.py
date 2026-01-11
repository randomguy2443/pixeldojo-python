"""Tests for custom exceptions."""

import pytest

from pixeldojo.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    InsufficientCreditsError,
    PixelDojoError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class TestPixelDojoError:
    """Tests for base exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        err = PixelDojoError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.message == "Something went wrong"
        assert err.status_code is None

    def test_error_with_status(self):
        """Test error with status code."""
        err = PixelDojoError("Bad request", status_code=400)
        assert str(err) == "[400] Bad request"
        assert err.status_code == 400

    def test_error_with_response_body(self):
        """Test error with response body."""
        body = {"error": "details", "code": "ERR001"}
        err = PixelDojoError("Failed", response_body=body)
        assert err.response_body == body

    def test_repr(self):
        """Test error representation."""
        err = PixelDojoError("Test", status_code=500)
        assert "PixelDojoError" in repr(err)
        assert "500" in repr(err)


class TestAuthenticationError:
    """Tests for authentication errors."""

    def test_default_message(self):
        """Test default error message."""
        err = AuthenticationError()
        assert "API key" in str(err)
        assert err.status_code == 401

    def test_custom_message(self):
        """Test custom error message."""
        err = AuthenticationError("Token expired")
        assert "Token expired" in str(err)


class TestInsufficientCreditsError:
    """Tests for insufficient credits errors."""

    def test_default_message(self):
        """Test default error message."""
        err = InsufficientCreditsError()
        assert "credits" in str(err).lower()
        assert err.status_code == 402

    def test_with_credits_info(self):
        """Test error with credit information."""
        err = InsufficientCreditsError(
            "Need more credits",
            credits_remaining=5.0,
            credits_required=10.0,
        )
        assert err.credits_remaining == 5.0
        assert err.credits_required == 10.0
        assert "5.0" in str(err)


class TestRateLimitError:
    """Tests for rate limit errors."""

    def test_default_message(self):
        """Test default error message."""
        err = RateLimitError()
        assert "rate limit" in str(err).lower()
        assert err.status_code == 429

    def test_with_retry_after(self):
        """Test error with retry-after."""
        err = RateLimitError("Slow down", retry_after=30.0)
        assert err.retry_after == 30.0
        assert "30" in str(err)


class TestAPIError:
    """Tests for general API errors."""

    def test_default_message(self):
        """Test default error message."""
        err = APIError()
        assert "failed" in str(err).lower()

    def test_with_status_code(self):
        """Test with status code."""
        err = APIError("Server error", status_code=500)
        assert err.status_code == 500


class TestValidationError:
    """Tests for validation errors."""

    def test_default_message(self):
        """Test default error message."""
        err = ValidationError()
        assert "validation" in str(err).lower()
        assert err.status_code == 422

    def test_with_field(self):
        """Test with field name."""
        err = ValidationError("Invalid value", field="prompt")
        assert err.field == "prompt"


class TestTimeoutError:
    """Tests for timeout errors."""

    def test_default_message(self):
        """Test default error message."""
        err = TimeoutError()
        assert "timed out" in str(err).lower()

    def test_with_timeout_value(self):
        """Test with timeout value."""
        err = TimeoutError("Request timed out", timeout=30.0)
        assert err.timeout == 30.0


class TestConnectionError:
    """Tests for connection errors."""

    def test_default_message(self):
        """Test default error message."""
        err = ConnectionError()
        assert "connect" in str(err).lower()


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_all_inherit_from_base(self):
        """Test all exceptions inherit from PixelDojoError."""
        exceptions = [
            AuthenticationError(),
            InsufficientCreditsError(),
            RateLimitError(),
            APIError(),
            ValidationError(),
            TimeoutError(),
            ConnectionError(),
        ]
        for exc in exceptions:
            assert isinstance(exc, PixelDojoError)

    def test_catchable_by_base(self):
        """Test exceptions can be caught by base class."""
        with pytest.raises(PixelDojoError):
            raise AuthenticationError()

        with pytest.raises(PixelDojoError):
            raise RateLimitError()
