"""
PixelDojo - Professional Python Client for AI Image Generation

A comprehensive Python package providing:
- Async/sync API client with automatic retries and connection pooling
- Beautiful CLI with rich terminal output
- Modern PySide6 desktop GUI application

Usage:
    # As a library
    from pixeldojo import PixelDojoClient

    async with PixelDojoClient(api_key="your-key") as client:
        result = await client.generate("A beautiful sunset over mountains")
        print(result.images[0].url)

    # CLI
    $ pixeldojo generate "A beautiful sunset" --model flux-pro

    # GUI
    $ pixeldojo-gui
"""

from pixeldojo.client import PixelDojoClient, PixelDojoSyncClient
from pixeldojo.config import Config, get_config
from pixeldojo.exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    PixelDojoError,
    RateLimitError,
)
from pixeldojo.models import (
    AspectRatio,
    GenerateRequest,
    GenerateResponse,
    ImageResult,
    Model,
)

__version__ = "1.0.0"
__author__ = "PixelDojo Team"
__all__ = [
    # Client
    "PixelDojoClient",
    "PixelDojoSyncClient",
    # Models
    "GenerateRequest",
    "GenerateResponse",
    "ImageResult",
    "Model",
    "AspectRatio",
    # Exceptions
    "PixelDojoError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "RateLimitError",
    "APIError",
    # Config
    "Config",
    "get_config",
]
