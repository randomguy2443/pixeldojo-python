# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-12

### Added

- **Core API Client**
  - Async-first design with `PixelDojoClient` using httpx
  - Synchronous wrapper `PixelDojoSyncClient` for convenience
  - Automatic retries with exponential backoff (tenacity)
  - Connection pooling for performance
  - Progress callbacks for UI integration

- **Pydantic Models**
  - Full type-safe request/response models
  - `Model` enum with all supported AI models (Flux, Qwen, WAN)
  - `AspectRatio` enum with dimension calculations
  - `GenerateRequest` and `GenerateResponse` with validation

- **Custom Exceptions**
  - `PixelDojoError` base exception
  - `AuthenticationError` for 401 responses
  - `InsufficientCreditsError` for 402 responses
  - `RateLimitError` for 429 responses
  - `APIError` for general failures

- **CLI Application**
  - Built with Typer and Rich for beautiful terminal output
  - `pixeldojo generate` - Generate images with full options
  - `pixeldojo models` - List available AI models
  - `pixeldojo ratios` - List aspect ratios
  - `pixeldojo config` - Manage API key and settings
  - `pixeldojo gui` - Launch desktop application
  - Multiple output formats: table, JSON, URLs, quiet
  - Progress bars and status updates
  - Image download support

- **Desktop GUI Application**
  - Modern PySide6-based interface
  - Dark theme with custom styling
  - Image gallery with thumbnails
  - Real-time generation with progress
  - Threaded async operations (non-blocking UI)
  - Context menu for save/copy operations
  - Credit balance display

- **Configuration System**
  - XDG-compliant paths (Linux)
  - Environment variable support (`PIXELDOJO_*`)
  - Secure API key storage with keyring
  - Configurable defaults for model, aspect ratio, etc.

- **Packaging**
  - Modern `pyproject.toml` with hatchling
  - Entry points for CLI (`pixeldojo`) and GUI (`pixeldojo-gui`)
  - Desktop integration files (.desktop, icon)

### Supported Models

| Model | Description |
|-------|-------------|
| `flux-pro` | High-quality professional image generation |
| `flux-1.1-pro` | Enhanced Flux Pro with improved quality |
| `flux-1.1-pro-ultra` | Maximum quality Flux model |
| `flux-dev` | Development/testing Flux model |
| `flux-dev-single-lora` | Flux Dev with single LoRA support |
| `qwen-image` | Optimized for text rendering in images |
| `wan-image` | Fast generation with cinematic style |

[1.0.0]: https://github.com/randomguy2443/pixeldojo-python/releases/tag/v1.0.0
