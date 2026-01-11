# PixelDojo

Professional Python client, CLI, and GUI for the PixelDojo AI Image Generation API.

## Features

- **Async API Client**: High-performance async client with sync wrapper, automatic retries, and connection pooling
- **Beautiful CLI**: Rich terminal output with progress bars, multiple output formats, and batch processing
- **Modern Desktop GUI**: PySide6-based application with dark theme, image gallery, and real-time generation
- **Type-Safe**: Full Pydantic models and type hints throughout
- **Secure**: Keyring-based API key storage

## Installation

```bash
# Install from source
pip install -e /home/ares/pixeldojo

# Or install dependencies manually
pip install httpx pydantic pydantic-settings tenacity typer rich PySide6 pillow platformdirs keyring aiofiles
```

## Quick Start

### As a Library

```python
from pixeldojo import PixelDojoClient

# Async usage (recommended)
async with PixelDojoClient(api_key="your-key") as client:
    result = await client.generate(
        "A beautiful sunset over mountains",
        model="flux-pro",
        aspect_ratio="16:9",
    )
    print(result.images[0].url)

# Sync usage
from pixeldojo import PixelDojoSyncClient

with PixelDojoSyncClient(api_key="your-key") as client:
    result = client.generate("A cyberpunk cityscape")
    for image in result.images:
        print(image.url)
```

### CLI

```bash
# Set API key (saved securely)
pixeldojo config set-key

# Generate an image
pixeldojo generate "A beautiful sunset over mountains"

# Generate with options
pixeldojo generate "Portrait of a cat" --model flux-1.1-pro --aspect-ratio 3:4 --num 2

# Output as JSON
pixeldojo generate "Logo design" --output json

# Download images
pixeldojo generate "Abstract art" --download ./output

# List available models
pixeldojo models

# List aspect ratios
pixeldojo ratios

# Launch GUI
pixeldojo gui
```

### Desktop GUI

```bash
# Launch directly
pixeldojo-gui

# Or via CLI
pixeldojo gui
```

## Available Models

| Model | Description |
|-------|-------------|
| `flux-pro` | High-quality professional image generation |
| `flux-1.1-pro` | Enhanced Flux Pro with improved quality |
| `flux-1.1-pro-ultra` | Maximum quality Flux model |
| `flux-dev` | Development/testing Flux model |
| `qwen-image` | Optimized for text rendering in images |
| `wan-image` | Fast generation with cinematic style |

## Aspect Ratios

- `1:1` - Square (1024x1024)
- `16:9` - Landscape wide
- `9:16` - Portrait tall
- `4:3` - Landscape standard
- `3:4` - Portrait standard
- `3:2` - Landscape photo
- `2:3` - Portrait photo

## Configuration

Environment variables:
- `PIXELDOJO_API_KEY`: API authentication key
- `PIXELDOJO_API_URL`: Base API URL (default: https://pixeldojo.ai/api/v1)
- `PIXELDOJO_TIMEOUT`: Request timeout in seconds (default: 120)
- `PIXELDOJO_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `PIXELDOJO_DEBUG`: Enable debug mode

## License

MIT License
