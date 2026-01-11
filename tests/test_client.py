"""Tests for API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pixeldojo.client import PixelDojoClient, PixelDojoSyncClient
from pixeldojo.exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
)
from pixeldojo.models import AspectRatio, GenerateResponse, Model


class TestPixelDojoClient:
    """Tests for async client."""

    @pytest.fixture
    def client(self, api_key: str) -> PixelDojoClient:
        """Create test client."""
        return PixelDojoClient(api_key=api_key)

    def test_client_creation(self, api_key: str):
        """Test client creation."""
        client = PixelDojoClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.is_authenticated is True

    def test_client_no_key(self):
        """Test client without API key."""
        with patch("pixeldojo.client.get_config") as mock:
            mock.return_value.api_key = ""
            mock.return_value.api_url = "https://pixeldojo.ai/api/v1"
            mock.return_value.timeout = 120.0
            mock.return_value.max_retries = 3
            mock.return_value.retry_delay = 1.0
            mock.return_value.max_connections = 10
            client = PixelDojoClient()
            assert client.is_authenticated is False

    def test_custom_url(self, api_key: str):
        """Test client with custom URL."""
        client = PixelDojoClient(
            api_key=api_key,
            api_url="https://custom.api.com/v2",
        )
        assert client.api_url == "https://custom.api.com/v2"

    @pytest.mark.asyncio
    async def test_generate_success(
        self, client: PixelDojoClient, sample_response: dict
    ):
        """Test successful generation."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_response

            async with client:
                result = await client.generate("A beautiful sunset")

            assert isinstance(result, GenerateResponse)
            assert len(result.images) == 1
            assert result.credits_used == 1.0
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_options(
        self, client: PixelDojoClient, sample_response: dict
    ):
        """Test generation with all options."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_response

            async with client:
                await client.generate(
                    "Test prompt",
                    model=Model.QWEN_IMAGE,
                    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
                    num_outputs=2,
                    seed=42,
                )

            call_args = mock_request.call_args
            json_data = call_args.kwargs["json"]
            assert json_data["model"] == "qwen-image"
            assert json_data["aspect_ratio"] == "16:9"
            assert json_data["num_outputs"] == 2
            assert json_data["seed"] == 42

    @pytest.mark.asyncio
    async def test_generate_with_progress(
        self, client: PixelDojoClient, sample_response: dict
    ):
        """Test generation with progress callback."""
        progress_calls = []

        def on_progress(status: str, pct: float):
            progress_calls.append((status, pct))

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = sample_response

            async with client:
                await client.generate("Test", on_progress=on_progress)

            assert len(progress_calls) > 0
            assert progress_calls[-1][1] == 1.0  # Final progress is 100%

    @pytest.mark.asyncio
    async def test_context_manager(self, api_key: str, sample_response: dict):
        """Test async context manager."""
        async with PixelDojoClient(api_key=api_key) as client:
            assert client._client is not None
        # Client should be closed after context
        assert client._client is None or client._client.is_closed


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def client(self, api_key: str) -> PixelDojoClient:
        """Create test client."""
        return PixelDojoClient(api_key=api_key, max_retries=0)

    @pytest.mark.asyncio
    async def test_authentication_error(self, client: PixelDojoClient):
        """Test 401 raises AuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}

        with pytest.raises(AuthenticationError):
            client._handle_response_error(mock_response)

    @pytest.mark.asyncio
    async def test_insufficient_credits_error(self, client: PixelDojoClient):
        """Test 402 raises InsufficientCreditsError."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": "Not enough credits",
            "credits_remaining": 0.5,
        }

        with pytest.raises(InsufficientCreditsError) as exc_info:
            client._handle_response_error(mock_response)

        assert exc_info.value.credits_remaining == 0.5

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, client: PixelDojoClient):
        """Test 429 raises RateLimitError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Too many requests"}
        mock_response.headers = {"Retry-After": "30"}

        with pytest.raises(RateLimitError) as exc_info:
            client._handle_response_error(mock_response)

        assert exc_info.value.retry_after == 30.0

    @pytest.mark.asyncio
    async def test_server_error(self, client: PixelDojoClient):
        """Test 5xx raises APIError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with pytest.raises(APIError) as exc_info:
            client._handle_response_error(mock_response)

        assert exc_info.value.status_code == 500


class TestPixelDojoSyncClient:
    """Tests for sync client."""

    def test_sync_client_creation(self, api_key: str):
        """Test sync client creation."""
        client = PixelDojoSyncClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.is_authenticated is True

    def test_sync_context_manager(self, api_key: str, sample_response: dict):
        """Test sync context manager."""
        with patch.object(
            PixelDojoClient, "generate", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = GenerateResponse.model_validate(sample_response)

            with PixelDojoSyncClient(api_key=api_key) as client:
                result = client.generate("Test prompt")

            assert isinstance(result, GenerateResponse)
