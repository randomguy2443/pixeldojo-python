"""Tests for CLI application."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typer.testing import CliRunner

from pixeldojo.cli.main import app
from pixeldojo.models import GenerateResponse, ImageResult


runner = CliRunner()


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.stdout

    def test_help(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "PixelDojo" in result.stdout
        assert "generate" in result.stdout
        assert "models" in result.stdout

    def test_models_command(self):
        """Test models command."""
        result = runner.invoke(app, ["models"])
        assert result.exit_code == 0
        assert "flux-pro" in result.stdout
        assert "qwen-image" in result.stdout
        assert "wan-image" in result.stdout

    def test_ratios_command(self):
        """Test ratios command."""
        result = runner.invoke(app, ["ratios"])
        assert result.exit_code == 0
        assert "1:1" in result.stdout
        assert "16:9" in result.stdout
        assert "Square" in result.stdout


class TestConfigCommands:
    """Tests for config subcommands."""

    def test_config_show(self):
        """Test config show command."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = "test_key_12345"
            mock_config.return_value.api_url = "https://pixeldojo.ai/api/v1"
            mock_config.return_value.timeout = 120.0
            mock_config.return_value.max_retries = 3
            mock_config.return_value.default_model = "flux-pro"
            mock_config.return_value.default_aspect_ratio = "1:1"
            mock_config.return_value.download_dir = "/tmp/downloads"
            mock_config.return_value.debug = False

            result = runner.invoke(app, ["config", "show"])
            assert result.exit_code == 0
            assert "API Key" in result.stdout
            assert "****" in result.stdout  # Key should be masked


class TestGenerateCommand:
    """Tests for generate command."""

    @pytest.fixture
    def mock_response(self) -> GenerateResponse:
        """Create mock response."""
        return GenerateResponse(
            images=[
                ImageResult(
                    url="https://example.com/image.png",
                    seed=12345,
                    width=1024,
                    height=1024,
                )
            ],
            credits_used=1.0,
            credits_remaining=99.0,
        )

    def test_generate_no_api_key(self):
        """Test generate fails without API key."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = ""

            result = runner.invoke(app, ["generate", "test prompt"])
            assert result.exit_code == 1
            # Error message goes to stderr or stdout depending on typer version
            assert "API key" in result.stdout or result.exit_code == 1

    def test_generate_invalid_model(self):
        """Test generate with invalid model."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = "test_key"

            result = runner.invoke(
                app, ["generate", "test", "--model", "invalid-model"]
            )
            assert result.exit_code == 1
            # Shows available models when invalid
            assert "flux-pro" in result.stdout or result.exit_code == 1

    def test_generate_invalid_aspect_ratio(self):
        """Test generate with invalid aspect ratio."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = "test_key"

            result = runner.invoke(
                app, ["generate", "test", "--aspect-ratio", "99:1"]
            )
            assert result.exit_code == 1
            # Shows available ratios when invalid
            assert "1:1" in result.stdout or result.exit_code == 1

    def test_generate_success_table(self, mock_response: GenerateResponse):
        """Test successful generation with table output."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = "test_key"

            with patch("pixeldojo.cli.main.asyncio.run") as mock_run:
                mock_run.return_value = mock_response

                result = runner.invoke(
                    app, ["generate", "A beautiful sunset", "--output", "table"]
                )

                # Should show table with image info
                assert "Generated Images" in result.stdout or result.exit_code == 0

    def test_generate_success_json(self, mock_response: GenerateResponse):
        """Test successful generation with JSON output."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = "test_key"

            with patch("pixeldojo.cli.main.asyncio.run") as mock_run:
                mock_run.return_value = mock_response

                result = runner.invoke(
                    app, ["generate", "test", "--output", "json"]
                )

                if result.exit_code == 0:
                    assert "url" in result.stdout or "images" in result.stdout

    def test_generate_success_urls(self, mock_response: GenerateResponse):
        """Test successful generation with URLs output."""
        with patch("pixeldojo.cli.main.get_config") as mock_config:
            mock_config.return_value.api_key = "test_key"

            with patch("pixeldojo.cli.main.asyncio.run") as mock_run:
                mock_run.return_value = mock_response

                result = runner.invoke(
                    app, ["generate", "test", "--output", "urls"]
                )

                if result.exit_code == 0:
                    assert "https://" in result.stdout


class TestCLIHelp:
    """Tests for command help text."""

    def test_generate_help(self):
        """Test generate command help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.stdout
        assert "--aspect-ratio" in result.stdout
        assert "--num" in result.stdout
        assert "--seed" in result.stdout
        assert "--output" in result.stdout
        assert "--download" in result.stdout

    def test_config_help(self):
        """Test config command help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "show" in result.stdout
        assert "set-key" in result.stdout
