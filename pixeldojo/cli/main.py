"""
PixelDojo CLI - Beautiful command-line interface for AI image generation.

Features:
- Rich terminal output with progress bars
- Multiple output formats (table, json, urls)
- Batch processing support
- API key management
- Image download and preview
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from pixeldojo import __version__
from pixeldojo.client import PixelDojoClient
from pixeldojo.config import get_config
from pixeldojo.exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    PixelDojoError,
    RateLimitError,
)
from pixeldojo.models import AspectRatio, GenerateResponse, Model

# Initialize console for rich output
console = Console()
err_console = Console(stderr=True)

# Create the main app
app = typer.Typer(
    name="pixeldojo",
    help="PixelDojo AI Image Generation CLI",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Output format options."""
    TABLE = "table"
    JSON = "json"
    URLS = "urls"
    QUIET = "quiet"


def print_banner() -> None:
    """Print the PixelDojo banner."""
    banner = Text()
    banner.append("PixelDojo", style="bold magenta")
    banner.append(" v" + __version__, style="dim")
    banner.append(" - AI Image Generation", style="cyan")
    console.print(Panel(banner, border_style="magenta"))


def print_error(message: str, exception: Exception | None = None) -> None:
    """Print an error message."""
    err_console.print(f"[bold red]Error:[/bold red] {message}")
    if exception and get_config().debug:
        err_console.print(f"[dim]{type(exception).__name__}: {exception}[/dim]")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def format_credits(used: float, remaining: float) -> str:
    """Format credits display."""
    return f"[cyan]{used:.2f}[/cyan] used, [green]{remaining:.2f}[/green] remaining"


def display_result_table(response: GenerateResponse, prompt: str) -> None:
    """Display generation result as a rich table."""
    table = Table(
        title="Generated Images",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("Dimensions", style="cyan")
    table.add_column("Seed", style="yellow")
    table.add_column("URL", style="green", overflow="fold")

    for i, image in enumerate(response.images, 1):
        table.add_row(
            str(i),
            image.dimensions,
            str(image.seed) if image.seed else "N/A",
            str(image.url),
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Prompt:[/dim] {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    credits_info = format_credits(response.credits_used, response.credits_remaining)
    console.print(f"[dim]Credits:[/dim] {credits_info}")


def display_result_json(response: GenerateResponse) -> None:
    """Display result as JSON."""
    output = {
        "images": [
            {
                "url": str(img.url),
                "seed": img.seed,
                "width": img.width,
                "height": img.height,
            }
            for img in response.images
        ],
        "credits_used": response.credits_used,
        "credits_remaining": response.credits_remaining,
    }
    console.print_json(json.dumps(output, indent=2))


def display_result_urls(response: GenerateResponse) -> None:
    """Display only image URLs."""
    for image in response.images:
        console.print(str(image.url))


@app.command()
def generate(
    prompt: Annotated[
        str,
        typer.Argument(
            help="Image description prompt",
            show_default=False,
        ),
    ],
    model: Annotated[
        str,
        typer.Option(
            "--model", "-m",
            help="AI model to use",
            show_default=True,
        ),
    ] = "flux-pro",
    aspect_ratio: Annotated[
        str,
        typer.Option(
            "--aspect-ratio", "-a",
            help="Image aspect ratio",
            show_default=True,
        ),
    ] = "1:1",
    num_outputs: Annotated[
        int,
        typer.Option(
            "--num", "-n",
            help="Number of images (1-4)",
            min=1,
            max=4,
            show_default=True,
        ),
    ] = 1,
    seed: Annotated[
        int | None,
        typer.Option(
            "--seed", "-s",
            help="Random seed for reproducibility",
        ),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--output", "-o",
            help="Output format",
            show_default=True,
        ),
    ] = OutputFormat.TABLE,
    download: Annotated[
        Path | None,
        typer.Option(
            "--download", "-d",
            help="Download images to directory",
            exists=False,
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key", "-k",
            help="API key (overrides config)",
            envvar="PIXELDOJO_API_KEY",
        ),
    ] = None,
) -> None:
    """
    Generate images from a text prompt.

    Examples:
        pixeldojo generate "A beautiful sunset over mountains"
        pixeldojo generate "Portrait of a cat" -m flux-1.1-pro -a 3:4
        pixeldojo generate "Cyberpunk city" -n 4 -o json
        pixeldojo generate "Logo design" -d ./output
    """
    config = get_config()
    key = api_key or config.api_key

    if not key:
        print_error("No API key configured. Use 'pixeldojo config set-key' to configure.")
        raise typer.Exit(1)

    # Validate model
    try:
        model_enum = Model(model)
    except ValueError:
        print_error(f"Invalid model: {model}")
        console.print("[dim]Available models:[/dim]")
        for m in Model:
            console.print(f"  [cyan]{m.value}[/cyan] - {m.description}")
        raise typer.Exit(1) from None

    # Validate aspect ratio
    try:
        ar_enum = AspectRatio(aspect_ratio)
    except ValueError:
        print_error(f"Invalid aspect ratio: {aspect_ratio}")
        console.print("[dim]Available ratios:[/dim]", ", ".join(ar.value for ar in AspectRatio))
        raise typer.Exit(1) from None

    async def run_generation() -> GenerateResponse:
        async with PixelDojoClient(api_key=key) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Generating...", total=100)

                def on_progress(status: str, pct: float) -> None:
                    progress.update(task, completed=int(pct * 100), description=status)

                return await client.generate(
                    prompt,
                    model=model_enum,
                    aspect_ratio=ar_enum,
                    num_outputs=num_outputs,
                    seed=seed,
                    on_progress=on_progress,
                )

    try:
        response = asyncio.run(run_generation())

        # Display results based on format
        if output_format == OutputFormat.TABLE:
            display_result_table(response, prompt)
        elif output_format == OutputFormat.JSON:
            display_result_json(response)
        elif output_format == OutputFormat.URLS:
            display_result_urls(response)
        # QUIET produces no output

        # Download if requested
        if download and response.images:
            download.mkdir(parents=True, exist_ok=True)
            console.print(f"\n[dim]Downloading to {download}...[/dim]")

            async def download_all() -> None:
                async with PixelDojoClient(api_key=key) as client:
                    for i, image in enumerate(response.images, 1):
                        filename = f"pixeldojo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
                        filepath = download / filename
                        await client.download_image(str(image.url), str(filepath))
                        console.print(f"  [green]Saved:[/green] {filepath}")

            asyncio.run(download_all())

    except AuthenticationError as e:
        print_error("Authentication failed. Check your API key.", e)
        raise typer.Exit(1) from None
    except InsufficientCreditsError as e:
        print_error(f"Insufficient credits. {e}", e)
        raise typer.Exit(1) from None
    except RateLimitError as e:
        print_error(f"Rate limit exceeded. {e}", e)
        raise typer.Exit(1) from None
    except PixelDojoError as e:
        print_error(str(e), e)
        raise typer.Exit(1) from None


@app.command()
def models() -> None:
    """List available AI models."""
    table = Table(
        title="Available Models",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")

    for model in Model:
        table.add_row(model.value, model.display_name, model.description)

    console.print(table)


@app.command()
def ratios() -> None:
    """List available aspect ratios."""
    table = Table(
        title="Available Aspect Ratios",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Ratio", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Dimensions", style="yellow")

    for ar in AspectRatio:
        w, h = ar.dimensions
        table.add_row(ar.value, ar.display_name, f"~{w}x{h}")

    console.print(table)


# Config subcommand group
config_app = typer.Typer(
    name="config",
    help="Manage configuration",
    no_args_is_help=True,
)
app.add_typer(config_app)


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    config = get_config()

    table = Table(
        title="Current Configuration",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Mask API key
    api_key_display = "****" + config.api_key[-4:] if len(config.api_key) > 4 else "(not set)"

    table.add_row("API Key", api_key_display)
    table.add_row("API URL", config.api_url)
    table.add_row("Timeout", f"{config.timeout}s")
    table.add_row("Max Retries", str(config.max_retries))
    table.add_row("Default Model", config.default_model)
    table.add_row("Default Aspect Ratio", config.default_aspect_ratio)
    table.add_row("Download Directory", str(config.download_dir))
    table.add_row("Debug Mode", str(config.debug))

    console.print(table)


@config_app.command("set-key")
def config_set_key(
    api_key: Annotated[
        str | None,
        typer.Argument(
            help="API key to save (prompts if not provided)",
        ),
    ] = None,
) -> None:
    """Save API key to secure storage."""
    if api_key is None:
        api_key = Prompt.ask("Enter your PixelDojo API key", password=True)

    if not api_key:
        print_error("API key cannot be empty")
        raise typer.Exit(1)

    config = get_config()
    config.save_api_key(api_key)
    print_success("API key saved to secure storage")


@config_app.command("clear-key")
def config_clear_key() -> None:
    """Remove API key from secure storage."""
    if Confirm.ask("Are you sure you want to remove your API key?"):
        config = get_config()
        config.delete_api_key()
        print_success("API key removed from secure storage")


@config_app.command("test")
def config_test() -> None:
    """Test API connection and authentication."""
    config = get_config()

    if not config.api_key:
        print_error("No API key configured")
        raise typer.Exit(1)

    console.print("[dim]Testing connection...[/dim]")

    async def test_connection() -> None:
        async with PixelDojoClient() as client:
            # Simple test - we'll catch auth errors
            response = await client.generate(
                "test",
                num_outputs=1,
            )
            print_success(f"Connection successful! Credits remaining: {response.credits_remaining}")

    try:
        asyncio.run(test_connection())
    except AuthenticationError:
        print_error("Authentication failed. Your API key may be invalid.")
        raise typer.Exit(1) from None
    except PixelDojoError as e:
        print_error(f"Connection test failed: {e}")
        raise typer.Exit(1) from None


@app.command()
def gui() -> None:
    """Launch the PixelDojo GUI application."""
    try:
        from pixeldojo.gui.main import main as gui_main
        gui_main()
    except ImportError as e:
        print_error(f"GUI dependencies not installed: {e}")
        console.print("[dim]Install with: pip install pixeldojo[gui][/dim]")
        raise typer.Exit(1) from None


@app.command()
def version() -> None:
    """Show version information."""
    print_banner()
    console.print(f"\n[dim]Python:[/dim] {sys.version.split()[0]}")
    console.print(f"[dim]Platform:[/dim] {sys.platform}")


def version_callback(value: bool) -> None:
    """Handle --version flag."""
    if value:
        console.print(f"pixeldojo {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version", "-V",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug mode",
            envvar="PIXELDOJO_DEBUG",
        ),
    ] = False,
) -> None:
    """
    PixelDojo CLI - Generate stunning AI images from the command line.

    Get started:
        1. Set your API key: pixeldojo config set-key
        2. Generate an image: pixeldojo generate "Your prompt here"
        3. Launch the GUI: pixeldojo gui

    For more help, run: pixeldojo <command> --help
    """
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    app()
