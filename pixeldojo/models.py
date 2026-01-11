"""
Pydantic models for PixelDojo API requests and responses.

Provides full type safety and validation for:
- Request parameters
- Response data
- Enums for models and aspect ratios
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class Model(str, Enum):
    """Available AI models for image generation."""

    # Flux models
    FLUX_PRO = "flux-pro"
    FLUX_1_1_PRO = "flux-1.1-pro"
    FLUX_1_1_PRO_ULTRA = "flux-1.1-pro-ultra"
    FLUX_DEV = "flux-dev"
    FLUX_DEV_SINGLE_LORA = "flux-dev-single-lora"

    # Other models
    QWEN_IMAGE = "qwen-image"  # Best for text rendering
    WAN_IMAGE = "wan-image"  # Fast cinematic generation

    @property
    def display_name(self) -> str:
        """Human-readable model name."""
        names = {
            self.FLUX_PRO: "Flux Pro",
            self.FLUX_1_1_PRO: "Flux 1.1 Pro",
            self.FLUX_1_1_PRO_ULTRA: "Flux 1.1 Pro Ultra",
            self.FLUX_DEV: "Flux Dev",
            self.FLUX_DEV_SINGLE_LORA: "Flux Dev (Single LoRA)",
            self.QWEN_IMAGE: "Qwen Image (Text Rendering)",
            self.WAN_IMAGE: "WAN Image (Fast Cinematic)",
        }
        return names.get(self, self.value)

    @property
    def description(self) -> str:
        """Model description."""
        descriptions = {
            self.FLUX_PRO: "High-quality professional image generation",
            self.FLUX_1_1_PRO: "Enhanced Flux Pro with improved quality",
            self.FLUX_1_1_PRO_ULTRA: "Maximum quality Flux model",
            self.FLUX_DEV: "Development/testing Flux model",
            self.FLUX_DEV_SINGLE_LORA: "Flux Dev with single LoRA support",
            self.QWEN_IMAGE: "Optimized for text rendering in images",
            self.WAN_IMAGE: "Fast generation with cinematic style",
        }
        return descriptions.get(self, "")


class AspectRatio(str, Enum):
    """Supported aspect ratios for image generation."""

    SQUARE = "1:1"
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    LANDSCAPE_4_3 = "4:3"
    PORTRAIT_3_4 = "3:4"
    LANDSCAPE_3_2 = "3:2"
    PORTRAIT_2_3 = "2:3"

    @property
    def display_name(self) -> str:
        """Human-readable aspect ratio name."""
        names = {
            self.SQUARE: "Square (1:1)",
            self.LANDSCAPE_16_9: "Landscape 16:9",
            self.PORTRAIT_9_16: "Portrait 9:16",
            self.LANDSCAPE_4_3: "Landscape 4:3",
            self.PORTRAIT_3_4: "Portrait 3:4",
            self.LANDSCAPE_3_2: "Landscape 3:2",
            self.PORTRAIT_2_3: "Portrait 2:3",
        }
        return names.get(self, self.value)

    @property
    def dimensions(self) -> tuple[int, int]:
        """Approximate dimensions at 1024px base."""
        dims = {
            self.SQUARE: (1024, 1024),
            self.LANDSCAPE_16_9: (1365, 768),
            self.PORTRAIT_9_16: (768, 1365),
            self.LANDSCAPE_4_3: (1182, 886),
            self.PORTRAIT_3_4: (886, 1182),
            self.LANDSCAPE_3_2: (1254, 836),
            self.PORTRAIT_2_3: (836, 1254),
        }
        return dims.get(self, (1024, 1024))


class GenerateRequest(BaseModel):
    """Request model for image generation."""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    prompt: Annotated[
        str,
        Field(
            min_length=1,
            max_length=4000,
            description="Image description prompt",
        ),
    ]
    model: Model = Field(
        default=Model.FLUX_PRO,
        description="AI model to use for generation",
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.SQUARE,
        description="Output image aspect ratio",
    )
    num_outputs: Annotated[
        int,
        Field(
            ge=1,
            le=4,
            default=1,
            description="Number of images to generate (1-4)",
        ),
    ]
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Ensure prompt is not just whitespace."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API request format."""
        data: dict[str, Any] = {
            "prompt": self.prompt,
            "model": self.model.value if isinstance(self.model, Model) else self.model,
            "aspect_ratio": (
                self.aspect_ratio.value
                if isinstance(self.aspect_ratio, AspectRatio)
                else self.aspect_ratio
            ),
            "num_outputs": self.num_outputs,
        }
        if self.seed is not None:
            data["seed"] = self.seed
        return data


class ImageResult(BaseModel):
    """Single generated image result."""

    model_config = ConfigDict(frozen=True)

    url: HttpUrl = Field(description="URL of the generated image")
    seed: int | None = Field(default=None, description="Seed used for generation")
    width: int | None = Field(default=None, description="Image width in pixels")
    height: int | None = Field(default=None, description="Image height in pixels")

    @property
    def dimensions(self) -> str:
        """Human-readable dimensions string."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"


class GenerateResponse(BaseModel):
    """Response model for image generation."""

    model_config = ConfigDict(frozen=True)

    images: list[ImageResult] = Field(
        default_factory=list,
        description="List of generated images",
    )
    credits_used: float = Field(
        default=0.0,
        description="Credits consumed by this request",
    )
    credits_remaining: float = Field(
        default=0.0,
        description="Remaining account credits",
    )

    @property
    def first_image(self) -> ImageResult | None:
        """Get the first image, if any."""
        return self.images[0] if self.images else None

    @property
    def image_urls(self) -> list[str]:
        """Get list of image URLs as strings."""
        return [str(img.url) for img in self.images]

    def __len__(self) -> int:
        """Return number of generated images."""
        return len(self.images)

    def __iter__(self):
        """Iterate over images."""
        return iter(self.images)

    def __getitem__(self, index: int) -> ImageResult:
        """Get image by index."""
        return self.images[index]


class GenerationJob(BaseModel):
    """Tracks a generation job with metadata."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Unique job identifier")
    request: GenerateRequest = Field(description="Original request")
    response: GenerateResponse | None = Field(
        default=None,
        description="Response when complete",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Job creation timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Job completion timestamp",
    )
    error: str | None = Field(default=None, description="Error message if failed")

    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.response is not None or self.error is not None

    @property
    def is_successful(self) -> bool:
        """Check if job completed successfully."""
        return self.response is not None and self.error is None

    @property
    def duration_seconds(self) -> float | None:
        """Get job duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
