"""
Background workers for async operations in the GUI.

Uses QThread and signals for thread-safe communication with the main UI.
"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, QThread, Signal

from pixeldojo.client import PixelDojoClient
from pixeldojo.exceptions import PixelDojoError
from pixeldojo.models import AspectRatio, GenerateResponse, Model


class GenerationWorker(QObject):
    """
    Worker for async image generation.

    Runs in a separate thread to keep the UI responsive.
    """

    # Signals
    started = Signal()
    progress = Signal(str, float)  # status, percentage
    finished = Signal(object)  # GenerateResponse
    error = Signal(str, object)  # error message, exception
    image_downloaded = Signal(str, bytes)  # url, data

    def __init__(
        self,
        api_key: str,
        prompt: str,
        model: str = "flux-pro",
        aspect_ratio: str = "1:1",
        num_outputs: int = 1,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key
        self.prompt = prompt
        self.model = model
        self.aspect_ratio = aspect_ratio
        self.num_outputs = num_outputs
        self.seed = seed
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._cancelled = True

    def run(self) -> None:
        """Execute the generation task."""
        if self._cancelled:
            return

        self.started.emit()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(self._generate())
                if not self._cancelled:
                    self.finished.emit(response)
            finally:
                loop.close()

        except PixelDojoError as e:
            if not self._cancelled:
                self.error.emit(str(e), e)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(f"Unexpected error: {e}", e)

    async def _generate(self) -> GenerateResponse:
        """Async generation with progress updates."""
        def on_progress(status: str, pct: float) -> None:
            if not self._cancelled:
                self.progress.emit(status, pct)

        async with PixelDojoClient(api_key=self.api_key) as client:
            return await client.generate(
                self.prompt,
                model=Model(self.model),
                aspect_ratio=AspectRatio(self.aspect_ratio),
                num_outputs=self.num_outputs,
                seed=self.seed,
                on_progress=on_progress,
            )


class ImageDownloadWorker(QObject):
    """Worker for downloading generated images."""

    finished = Signal(str, bytes)  # url, data
    error = Signal(str, str)  # url, error message

    def __init__(self, api_key: str, url: str) -> None:
        super().__init__()
        self.api_key = api_key
        self.url = url

    def run(self) -> None:
        """Download the image."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                data = loop.run_until_complete(self._download())
                self.finished.emit(self.url, data)
            finally:
                loop.close()

        except Exception as e:
            self.error.emit(self.url, str(e))

    async def _download(self) -> bytes:
        """Async image download."""
        async with PixelDojoClient(api_key=self.api_key) as client:
            return await client.download_image(self.url)


def run_worker(worker: QObject) -> QThread:
    """
    Create and start a QThread for a worker.

    Args:
        worker: Worker object with a run() method

    Returns:
        Started QThread instance
    """
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.start()
    return thread
