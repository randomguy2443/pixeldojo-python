"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from pixeldojo.models import (
    Model,
    AspectRatio,
    GenerateRequest,
    GenerateResponse,
    ImageResult,
)


class TestModel:
    """Tests for Model enum."""

    def test_all_models_exist(self):
        """Verify all expected models are defined."""
        expected = [
            "flux-pro",
            "flux-1.1-pro",
            "flux-1.1-pro-ultra",
            "flux-dev",
            "flux-dev-single-lora",
            "qwen-image",
            "wan-image",
        ]
        actual = [m.value for m in Model]
        assert actual == expected

    def test_model_display_name(self):
        """Test display names are set."""
        assert Model.FLUX_PRO.display_name == "Flux Pro"
        assert Model.QWEN_IMAGE.display_name == "Qwen Image (Text Rendering)"

    def test_model_description(self):
        """Test descriptions are set."""
        assert "professional" in Model.FLUX_PRO.description.lower()
        assert "text" in Model.QWEN_IMAGE.description.lower()


class TestAspectRatio:
    """Tests for AspectRatio enum."""

    def test_all_ratios_exist(self):
        """Verify all expected aspect ratios are defined."""
        expected = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]
        actual = [ar.value for ar in AspectRatio]
        assert actual == expected

    def test_dimensions(self):
        """Test dimension calculations."""
        assert AspectRatio.SQUARE.dimensions == (1024, 1024)
        assert AspectRatio.LANDSCAPE_16_9.dimensions[0] > AspectRatio.LANDSCAPE_16_9.dimensions[1]
        assert AspectRatio.PORTRAIT_9_16.dimensions[0] < AspectRatio.PORTRAIT_9_16.dimensions[1]

    def test_display_name(self):
        """Test display names."""
        assert "Square" in AspectRatio.SQUARE.display_name
        assert "16:9" in AspectRatio.LANDSCAPE_16_9.display_name


class TestGenerateRequest:
    """Tests for GenerateRequest model."""

    def test_minimal_request(self):
        """Test creating request with just prompt."""
        req = GenerateRequest(prompt="A beautiful sunset")
        assert req.prompt == "A beautiful sunset"
        assert req.model == Model.FLUX_PRO
        assert req.aspect_ratio == AspectRatio.SQUARE
        assert req.num_outputs == 1
        assert req.seed is None

    def test_full_request(self):
        """Test creating request with all options."""
        req = GenerateRequest(
            prompt="A cyberpunk city",
            model=Model.FLUX_1_1_PRO,
            aspect_ratio=AspectRatio.LANDSCAPE_16_9,
            num_outputs=4,
            seed=42,
        )
        assert req.prompt == "A cyberpunk city"
        assert req.model == Model.FLUX_1_1_PRO
        assert req.aspect_ratio == AspectRatio.LANDSCAPE_16_9
        assert req.num_outputs == 4
        assert req.seed == 42

    def test_prompt_strip_whitespace(self):
        """Test that prompt whitespace is stripped."""
        req = GenerateRequest(prompt="  test prompt  ")
        assert req.prompt == "test prompt"

    def test_empty_prompt_fails(self):
        """Test that empty prompt raises error."""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="")

    def test_whitespace_only_prompt_fails(self):
        """Test that whitespace-only prompt raises error."""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="   ")

    def test_num_outputs_range(self):
        """Test num_outputs validation."""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="test", num_outputs=0)
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="test", num_outputs=5)

    def test_to_api_dict(self):
        """Test conversion to API format."""
        req = GenerateRequest(
            prompt="test",
            model=Model.QWEN_IMAGE,
            aspect_ratio=AspectRatio.PORTRAIT_3_4,
            num_outputs=2,
            seed=123,
        )
        data = req.to_api_dict()
        assert data["prompt"] == "test"
        assert data["model"] == "qwen-image"
        assert data["aspect_ratio"] == "3:4"
        assert data["num_outputs"] == 2
        assert data["seed"] == 123

    def test_to_api_dict_no_seed(self):
        """Test API dict without seed."""
        req = GenerateRequest(prompt="test")
        data = req.to_api_dict()
        assert "seed" not in data


class TestImageResult:
    """Tests for ImageResult model."""

    def test_create_image_result(self):
        """Test creating image result."""
        img = ImageResult(
            url="https://example.com/image.png",
            seed=42,
            width=1024,
            height=768,
        )
        assert str(img.url) == "https://example.com/image.png"
        assert img.seed == 42
        assert img.dimensions == "1024x768"

    def test_dimensions_unknown(self):
        """Test dimensions when not provided."""
        img = ImageResult(url="https://example.com/image.png")
        assert img.dimensions == "Unknown"

    def test_immutable(self):
        """Test that ImageResult is immutable."""
        img = ImageResult(url="https://example.com/image.png")
        with pytest.raises(ValidationError):
            img.seed = 42


class TestGenerateResponse:
    """Tests for GenerateResponse model."""

    def test_create_response(self, sample_response: dict):
        """Test creating response from API data."""
        resp = GenerateResponse.model_validate(sample_response)
        assert len(resp.images) == 1
        assert resp.credits_used == 1.0
        assert resp.credits_remaining == 99.0

    def test_first_image(self, sample_response: dict):
        """Test first_image property."""
        resp = GenerateResponse.model_validate(sample_response)
        assert resp.first_image is not None
        assert resp.first_image.seed == 12345

    def test_first_image_empty(self):
        """Test first_image when no images."""
        resp = GenerateResponse(images=[], credits_used=0, credits_remaining=100)
        assert resp.first_image is None

    def test_image_urls(self, sample_response_multiple: dict):
        """Test image_urls property."""
        resp = GenerateResponse.model_validate(sample_response_multiple)
        urls = resp.image_urls
        assert len(urls) == 2
        assert all(url.startswith("https://") for url in urls)

    def test_len(self, sample_response_multiple: dict):
        """Test __len__."""
        resp = GenerateResponse.model_validate(sample_response_multiple)
        assert len(resp) == 2

    def test_iteration(self, sample_response_multiple: dict):
        """Test __iter__."""
        resp = GenerateResponse.model_validate(sample_response_multiple)
        images = list(resp)
        assert len(images) == 2

    def test_indexing(self, sample_response_multiple: dict):
        """Test __getitem__."""
        resp = GenerateResponse.model_validate(sample_response_multiple)
        assert resp[0].seed == 12345
        assert resp[1].seed == 12346
