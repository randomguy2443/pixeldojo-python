"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def api_key() -> str:
    """Test API key."""
    return "pd_test_key_12345"


@pytest.fixture
def mock_config(api_key: str):
    """Mock configuration."""
    with patch("pixeldojo.config.get_config") as mock:
        config = MagicMock()
        config.api_key = api_key
        config.api_url = "https://pixeldojo.ai/api/v1"
        config.timeout = 30.0
        config.max_retries = 3
        config.retry_delay = 1.0
        config.max_connections = 10
        config.debug = False
        config.default_model = "flux-pro"
        config.default_aspect_ratio = "1:1"
        mock.return_value = config
        yield config


@pytest.fixture
def sample_response() -> dict:
    """Sample API response."""
    return {
        "images": [
            {
                "url": "https://temp.pixeldojo.ai/test/image1.png",
                "seed": 12345,
                "width": 1024,
                "height": 1024,
            }
        ],
        "credits_used": 1.0,
        "credits_remaining": 99.0,
    }


@pytest.fixture
def sample_response_multiple() -> dict:
    """Sample API response with multiple images."""
    return {
        "images": [
            {
                "url": "https://temp.pixeldojo.ai/test/image1.png",
                "seed": 12345,
                "width": 1024,
                "height": 1024,
            },
            {
                "url": "https://temp.pixeldojo.ai/test/image2.png",
                "seed": 12346,
                "width": 1024,
                "height": 1024,
            },
        ],
        "credits_used": 2.0,
        "credits_remaining": 98.0,
    }
