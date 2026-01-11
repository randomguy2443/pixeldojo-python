"""
PixelDojo API Client - Async-first with sync wrapper.

Features:
- Async and sync interfaces
- Automatic retries with exponential backoff
- Connection pooling
- Comprehensive error handling
- Type-safe request/response handling
- Progress callbacks for GUI integration
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Iterator
from uuid import uuid4

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from pixeldojo.config import Config, get_config
from pixeldojo.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    InsufficientCreditsError,
    PixelDojoError,
    RateLimitError,
    TimeoutError,
)
from pixeldojo.models import (
    AspectRatio,
    GenerateRequest,
    GenerateResponse,
    GenerationJob,
    ImageResult,
    Model,
)

logger = logging.getLogger(__name__)


# Type alias for progress callbacks
ProgressCallback = Callable[[str, float], None]


class PixelDojoClient:
    """
    Async HTTP client for PixelDojo API.

    Example:
        async with PixelDojoClient(api_key="your-key") as client:
            result = await client.generate("A beautiful sunset")
            print(result.images[0].url)
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        config: Config | None = None,
    ) -> None:
        """
        Initialize the PixelDojo client.

        Args:
            api_key: API authentication key (overrides config)
            api_url: Base API URL (overrides config)
            timeout: Request timeout in seconds (overrides config)
            max_retries: Maximum retry attempts (overrides config)
            config: Custom config instance (uses default if None)
        """
        self._config = config or get_config()
        self._api_key = api_key or self._config.api_key
        self._api_url = api_url or self._config.api_url
        self._timeout = timeout or self._config.timeout
        self._max_retries = max_retries if max_retries is not None else self._config.max_retries
        self._client: httpx.AsyncClient | None = None
        self._owned_client = False

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._api_key

    @property
    def api_url(self) -> str:
        """Get the API URL."""
        return self._api_url

    @property
    def is_authenticated(self) -> bool:
        """Check if client has an API key configured."""
        return bool(self._api_key)

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with authentication."""
        if not self._api_key:
            raise AuthenticationError("API key not configured")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PixelDojo-Python/1.0.0",
            "Accept": "application/json",
        }

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._api_url,
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(
                    max_connections=self._config.max_connections,
                    max_keepalive_connections=self._config.max_connections // 2,
                ),
                follow_redirects=True,
            )
            self._owned_client = True
        return self._client

    async def __aenter__(self) -> "PixelDojoClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and self._owned_client:
            await self._client.aclose()
            self._client = None

    def _handle_response_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        status = response.status_code

        try:
            body = response.json()
        except Exception:
            body = {"error": response.text}

        error_msg = body.get("error", body.get("message", "Unknown error"))

        if status == 401:
            raise AuthenticationError(
                f"Authentication failed: {error_msg}",
                response_body=body,
            )
        elif status == 402:
            raise InsufficientCreditsError(
                f"Insufficient credits: {error_msg}",
                credits_remaining=body.get("credits_remaining"),
                response_body=body,
            )
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                f"Rate limit exceeded: {error_msg}",
                retry_after=float(retry_after) if retry_after else None,
                response_body=body,
            )
        elif status == 422:
            raise PixelDojoError(
                f"Validation error: {error_msg}",
                status_code=status,
                response_body=body,
            )
        elif status >= 500:
            raise APIError(
                f"Server error: {error_msg}",
                status_code=status,
                response_body=body,
            )
        else:
            raise APIError(
                f"Request failed: {error_msg}",
                status_code=status,
                response_body=body,
            )

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic."""
        client = await self._ensure_client()

        @retry(
            retry=retry_if_exception_type((httpx.TransportError, APIError)),
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=self._config.retry_delay, min=1, max=30),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _do_request() -> dict[str, Any]:
            try:
                response = await client.request(
                    method,
                    endpoint,
                    headers=self._get_headers(),
                    **kwargs,
                )
            except httpx.TimeoutException as e:
                raise TimeoutError(
                    f"Request timed out after {self._timeout}s",
                    timeout=self._timeout,
                ) from e
            except httpx.TransportError as e:
                raise ConnectionError(f"Connection failed: {e}") from e

            if response.status_code >= 400:
                self._handle_response_error(response)

            return response.json()

        return await _do_request()

    async def generate(
        self,
        prompt: str,
        *,
        model: Model | str = Model.FLUX_PRO,
        aspect_ratio: AspectRatio | str = AspectRatio.SQUARE,
        num_outputs: int = 1,
        seed: int | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> GenerateResponse:
        """
        Generate images from a text prompt.

        Args:
            prompt: Image description
            model: AI model to use
            aspect_ratio: Output aspect ratio
            num_outputs: Number of images to generate (1-4)
            seed: Random seed for reproducibility
            on_progress: Optional callback for progress updates

        Returns:
            GenerateResponse with generated images and credit info

        Raises:
            AuthenticationError: If API key is invalid
            InsufficientCreditsError: If account has insufficient credits
            RateLimitError: If rate limit is exceeded
            APIError: For other API errors
        """
        # Build and validate request
        request = GenerateRequest(
            prompt=prompt,
            model=model if isinstance(model, Model) else Model(model),
            aspect_ratio=(
                aspect_ratio
                if isinstance(aspect_ratio, AspectRatio)
                else AspectRatio(aspect_ratio)
            ),
            num_outputs=num_outputs,
            seed=seed,
        )

        if on_progress:
            on_progress("Sending request...", 0.1)

        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.debug(f"Request: {request.to_api_dict()}")

        if on_progress:
            on_progress("Waiting for generation...", 0.3)

        response_data = await self._request(
            "POST",
            "/generate",
            json=request.to_api_dict(),
        )

        if on_progress:
            on_progress("Processing response...", 0.9)

        response = GenerateResponse.model_validate(response_data)

        logger.info(
            f"Generated {len(response.images)} images, "
            f"credits used: {response.credits_used}"
        )

        if on_progress:
            on_progress("Complete!", 1.0)

        return response

    async def generate_batch(
        self,
        prompts: list[str],
        *,
        model: Model | str = Model.FLUX_PRO,
        aspect_ratio: AspectRatio | str = AspectRatio.SQUARE,
        num_outputs: int = 1,
        max_concurrent: int = 3,
        on_progress: Callable[[int, int, GenerateResponse | None], None] | None = None,
    ) -> list[GenerateResponse | PixelDojoError]:
        """
        Generate images for multiple prompts concurrently.

        Args:
            prompts: List of image descriptions
            model: AI model to use
            aspect_ratio: Output aspect ratio
            num_outputs: Number of images per prompt
            max_concurrent: Maximum concurrent requests
            on_progress: Callback(completed, total, response_or_none)

        Returns:
            List of responses or errors for each prompt
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results: list[GenerateResponse | PixelDojoError] = []
        completed = 0

        async def generate_one(prompt: str) -> GenerateResponse | PixelDojoError:
            nonlocal completed
            async with semaphore:
                try:
                    result = await self.generate(
                        prompt,
                        model=model,
                        aspect_ratio=aspect_ratio,
                        num_outputs=num_outputs,
                    )
                    completed += 1
                    if on_progress:
                        on_progress(completed, len(prompts), result)
                    return result
                except PixelDojoError as e:
                    completed += 1
                    if on_progress:
                        on_progress(completed, len(prompts), None)
                    return e

        tasks = [generate_one(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results

    async def download_image(
        self,
        url: str,
        destination: str | None = None,
    ) -> bytes:
        """
        Download a generated image.

        Args:
            url: Image URL
            destination: Optional file path to save to

        Returns:
            Image bytes
        """
        client = await self._ensure_client()
        response = await client.get(url)
        response.raise_for_status()

        content = response.content

        if destination:
            from pathlib import Path
            import aiofiles

            path = Path(destination)
            path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, "wb") as f:
                await f.write(content)
            logger.info(f"Image saved to {destination}")

        return content


class PixelDojoSyncClient:
    """
    Synchronous wrapper for PixelDojoClient.

    Example:
        with PixelDojoSyncClient(api_key="your-key") as client:
            result = client.generate("A beautiful sunset")
            print(result.images[0].url)
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize the sync client with same options as async client."""
        self._async_client = PixelDojoClient(
            api_key=api_key,
            api_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
            config=config,
        )
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for sync operations."""
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                "Cannot use sync client from within an async context. "
                "Use PixelDojoClient instead."
            )
        except RuntimeError:
            pass

        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def _run(self, coro: Any) -> Any:
        """Run coroutine in event loop."""
        return self._get_loop().run_until_complete(coro)

    def __enter__(self) -> "PixelDojoSyncClient":
        """Context manager entry."""
        self._run(self._async_client.__aenter__())
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self._run(self._async_client.__aexit__(exc_type, exc_val, exc_tb))
        if self._loop:
            self._loop.close()
            self._loop = None

    def close(self) -> None:
        """Close the client."""
        self._run(self._async_client.close())
        if self._loop:
            self._loop.close()
            self._loop = None

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._async_client.api_key

    @property
    def is_authenticated(self) -> bool:
        """Check if client has an API key configured."""
        return self._async_client.is_authenticated

    def generate(
        self,
        prompt: str,
        *,
        model: Model | str = Model.FLUX_PRO,
        aspect_ratio: AspectRatio | str = AspectRatio.SQUARE,
        num_outputs: int = 1,
        seed: int | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> GenerateResponse:
        """Generate images from a text prompt (sync version)."""
        return self._run(
            self._async_client.generate(
                prompt,
                model=model,
                aspect_ratio=aspect_ratio,
                num_outputs=num_outputs,
                seed=seed,
                on_progress=on_progress,
            )
        )

    def download_image(
        self,
        url: str,
        destination: str | None = None,
    ) -> bytes:
        """Download a generated image (sync version)."""
        return self._run(
            self._async_client.download_image(url, destination)
        )


# Convenience function for quick one-off generation
async def generate(
    prompt: str,
    *,
    api_key: str | None = None,
    model: Model | str = Model.FLUX_PRO,
    aspect_ratio: AspectRatio | str = AspectRatio.SQUARE,
    num_outputs: int = 1,
    seed: int | None = None,
) -> GenerateResponse:
    """
    Quick function to generate images without managing a client.

    Example:
        images = await pixeldojo.generate("A sunset", api_key="...")
    """
    async with PixelDojoClient(api_key=api_key) as client:
        return await client.generate(
            prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            num_outputs=num_outputs,
            seed=seed,
        )
