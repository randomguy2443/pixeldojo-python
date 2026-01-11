"""
Custom widgets for PixelDojo GUI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QMenu,
    QFileDialog,
    QApplication,
)


class ImageCard(QFrame):
    """
    Card widget for displaying a generated image with metadata.
    """

    clicked = Signal(object)  # Emits the ImageCard instance
    download_requested = Signal(str)  # Emits URL
    copy_requested = Signal(str)  # Emits URL

    def __init__(
        self,
        image_url: str,
        image_data: bytes | None = None,
        seed: int | None = None,
        dimensions: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.image_url = image_url
        self.image_data = image_data
        self.seed = seed
        self.dimensions = dimensions

        self.setObjectName("imageFrame")
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(180, 180)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self.image_label, stretch=1)

        # Info bar
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        if self.dimensions:
            dim_label = QLabel(self.dimensions)
            dim_label.setObjectName("subLabel")
            info_layout.addWidget(dim_label)

        if self.seed is not None:
            seed_label = QLabel(f"Seed: {self.seed}")
            seed_label.setObjectName("subLabel")
            info_layout.addWidget(seed_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Set placeholder
        self._set_placeholder()

    def _set_placeholder(self) -> None:
        """Set placeholder while loading."""
        self.image_label.setText("Loading...")
        self.image_label.setStyleSheet("color: #888;")

    def set_image(self, data: bytes) -> None:
        """Set the image from bytes data."""
        self.image_data = data
        image = QImage()
        if image.loadFromData(data):
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.image_label.setStyleSheet("")
        else:
            self.image_label.setText("Failed to load")

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Set the image from a QPixmap."""
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        """Handle resize to rescale image."""
        super().resizeEvent(event)
        if self.image_data:
            self.set_image(self.image_data)

    def mousePressEvent(self, event) -> None:
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Show context menu."""
        menu = QMenu(self)

        copy_action = menu.addAction("Copy URL")
        copy_action.triggered.connect(lambda: self.copy_requested.emit(self.image_url))

        download_action = menu.addAction("Save Image...")
        download_action.triggered.connect(self._save_image)

        if self.seed is not None:
            menu.addSeparator()
            copy_seed = menu.addAction(f"Copy Seed ({self.seed})")
            copy_seed.triggered.connect(self._copy_seed)

        menu.exec(event.globalPos())

    def _save_image(self) -> None:
        """Save image to file."""
        if not self.image_data:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            f"pixeldojo_image.png",
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)",
        )

        if filename:
            Path(filename).write_bytes(self.image_data)

    def _copy_seed(self) -> None:
        """Copy seed to clipboard."""
        if self.seed is not None:
            QApplication.clipboard().setText(str(self.seed))


class ImageGallery(QWidget):
    """
    Gallery widget for displaying multiple generated images.
    """

    image_selected = Signal(object)  # Emits ImageCard

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cards: list[ImageCard] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the gallery UI."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(15)
        self.layout.addStretch()

    def clear(self) -> None:
        """Clear all images from the gallery."""
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()

        # Remove all items from layout
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_image(
        self,
        url: str,
        data: bytes | None = None,
        seed: int | None = None,
        dimensions: str = "",
    ) -> ImageCard:
        """Add an image to the gallery."""
        card = ImageCard(
            image_url=url,
            image_data=data,
            seed=seed,
            dimensions=dimensions,
            parent=self,
        )

        if data:
            card.set_image(data)

        card.clicked.connect(lambda c: self.image_selected.emit(c))

        # Insert before the stretch
        self.layout.insertWidget(len(self.cards), card)
        self.cards.append(card)

        return card

    def get_card(self, url: str) -> ImageCard | None:
        """Get a card by URL."""
        for card in self.cards:
            if card.image_url == url:
                return card
        return None


class PromptInput(QWidget):
    """
    Enhanced prompt input widget with character count.
    """

    submitted = Signal(str)  # Emits prompt text

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        from PySide6.QtWidgets import QTextEdit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Text input
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("promptInput")
        self.text_edit.setPlaceholderText(
            "Describe the image you want to generate...\n\n"
            "Tips:\n"
            "- Be specific about style, colors, and composition\n"
            "- Mention lighting and mood\n"
            "- Include relevant artistic references"
        )
        self.text_edit.setMinimumHeight(100)
        self.text_edit.setMaximumHeight(200)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)

        # Character count
        self.char_label = QLabel("0 / 4000")
        self.char_label.setObjectName("subLabel")
        self.char_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.char_label)

    def _on_text_changed(self) -> None:
        """Update character count."""
        text = self.text_edit.toPlainText()
        count = len(text)
        self.char_label.setText(f"{count} / 4000")

        if count > 4000:
            self.char_label.setStyleSheet("color: #e74c3c;")
        else:
            self.char_label.setStyleSheet("")

    def get_text(self) -> str:
        """Get the prompt text."""
        return self.text_edit.toPlainText().strip()

    def set_text(self, text: str) -> None:
        """Set the prompt text."""
        self.text_edit.setPlainText(text)

    def clear(self) -> None:
        """Clear the input."""
        self.text_edit.clear()

    def is_valid(self) -> bool:
        """Check if prompt is valid."""
        text = self.get_text()
        return bool(text) and len(text) <= 4000


class CreditDisplay(QWidget):
    """Widget to display credit balance."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Credits: --")
        self.label.setStyleSheet("color: #00d4aa; font-weight: bold;")
        layout.addWidget(self.label)

    def set_credits(self, remaining: float) -> None:
        """Update the credit display."""
        self.label.setText(f"Credits: {remaining:.2f}")

        # Color based on balance
        if remaining < 10:
            self.label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif remaining < 50:
            self.label.setStyleSheet("color: #f39c12; font-weight: bold;")
        else:
            self.label.setStyleSheet("color: #00d4aa; font-weight: bold;")
