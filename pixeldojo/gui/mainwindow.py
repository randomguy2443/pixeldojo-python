"""
Main window for PixelDojo GUI application.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Slot
from PySide6.QtGui import QAction, QCloseEvent, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pixeldojo import __version__
from pixeldojo.config import get_config, reload_config
from pixeldojo.gui.widgets import (
    CreditDisplay,
    ImageCard,
    ImageGallery,
    PromptInput,
)
from pixeldojo.gui.workers import GenerationWorker, ImageDownloadWorker, run_worker
from pixeldojo.models import AspectRatio, GenerateResponse, Model


class MainWindow(QMainWindow):
    """
    Main application window for PixelDojo.
    """

    def __init__(self) -> None:
        super().__init__()
        self.config = get_config()
        self.current_worker: GenerationWorker | None = None
        self.worker_thread: QThread | None = None
        self.download_threads: list[QThread] = []
        self.generation_history: list[dict] = []

        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()
        self._check_api_key()

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"PixelDojo Studio v{__version__}")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _setup_menu(self) -> None:
        """Set up menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        save_action = QAction("&Save All Images...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_all_images)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        clear_action = QAction("&Clear Gallery", self)
        clear_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_L))
        clear_action.triggered.connect(self._clear_gallery)
        edit_menu.addAction(clear_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        api_key_action = QAction("Set &API Key...", self)
        api_key_action.triggered.connect(self._set_api_key)
        settings_menu.addAction(api_key_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self) -> None:
        """Set up main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel - Controls
        left_panel = self._create_control_panel()
        left_panel.setFixedWidth(400)
        main_layout.addWidget(left_panel)

        # Right panel - Gallery
        right_panel = self._create_gallery_panel()
        main_layout.addWidget(right_panel, stretch=1)

    def _create_control_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QFrame()
        panel.setObjectName("controlPanel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # Title
        title = QLabel("Generate Image")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #6c5ce7;")
        layout.addWidget(title)

        # Prompt input
        prompt_group = QGroupBox("Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        self.prompt_input = PromptInput()
        prompt_layout.addWidget(self.prompt_input)
        layout.addWidget(prompt_group)

        # Model selection
        model_group = QGroupBox("Model")
        model_layout = QVBoxLayout(model_group)

        self.model_combo = QComboBox()
        for model in Model:
            self.model_combo.addItem(model.display_name, model.value)
        self.model_combo.setCurrentText(Model.FLUX_PRO.display_name)
        model_layout.addWidget(self.model_combo)

        # Model description
        self.model_desc = QLabel(Model.FLUX_PRO.description)
        self.model_desc.setObjectName("subLabel")
        self.model_desc.setWordWrap(True)
        self.model_combo.currentIndexChanged.connect(self._update_model_description)
        model_layout.addWidget(self.model_desc)

        layout.addWidget(model_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # Aspect ratio
        ar_layout = QHBoxLayout()
        ar_label = QLabel("Aspect Ratio:")
        ar_layout.addWidget(ar_label)
        self.aspect_combo = QComboBox()
        for ar in AspectRatio:
            self.aspect_combo.addItem(ar.display_name, ar.value)
        ar_layout.addWidget(self.aspect_combo, stretch=1)
        options_layout.addLayout(ar_layout)

        # Number of outputs
        num_layout = QHBoxLayout()
        num_label = QLabel("Images:")
        num_layout.addWidget(num_label)
        self.num_spin = QSpinBox()
        self.num_spin.setRange(1, 4)
        self.num_spin.setValue(1)
        num_layout.addWidget(self.num_spin, stretch=1)
        options_layout.addLayout(num_layout)

        # Seed
        seed_layout = QHBoxLayout()
        seed_label = QLabel("Seed:")
        seed_layout.addWidget(seed_label)
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Random (leave empty)")
        seed_layout.addWidget(self.seed_input, stretch=1)
        options_layout.addLayout(seed_layout)

        layout.addWidget(options_group)

        # Generate button
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.generate_btn.clicked.connect(self._on_generate)
        layout.addWidget(self.generate_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("subLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Credits display
        self.credit_display = CreditDisplay()
        layout.addWidget(self.credit_display)

        return panel

    def _create_gallery_panel(self) -> QWidget:
        """Create the right gallery panel."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()
        title = QLabel("Gallery")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self._clear_gallery)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Gallery scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gallery = ImageGallery()
        self.gallery.image_selected.connect(self._on_image_selected)
        scroll.setWidget(self.gallery)

        layout.addWidget(scroll, stretch=1)

        # Preview area (shown when image selected)
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("imageFrame")
        self.preview_frame.setMinimumHeight(300)
        self.preview_frame.setVisible(False)
        preview_layout = QVBoxLayout(self.preview_frame)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(self.preview_frame)

        return panel

    def _setup_statusbar(self) -> None:
        """Set up status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _check_api_key(self) -> None:
        """Check if API key is configured."""
        if not self.config.api_key:
            QMessageBox.warning(
                self,
                "API Key Required",
                "No API key configured.\n\n"
                "Please go to Settings > Set API Key to configure your PixelDojo API key.",
            )

    def _update_model_description(self) -> None:
        """Update model description when selection changes."""
        model_value = self.model_combo.currentData()
        try:
            model = Model(model_value)
            self.model_desc.setText(model.description)
        except ValueError:
            self.model_desc.setText("")

    @Slot()
    def _on_generate(self) -> None:
        """Handle generate button click."""
        if not self.prompt_input.is_valid():
            QMessageBox.warning(
                self,
                "Invalid Prompt",
                "Please enter a valid prompt (1-4000 characters).",
            )
            return

        if not self.config.api_key:
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please configure your API key in Settings > Set API Key.",
            )
            return

        # Get parameters
        prompt = self.prompt_input.get_text()
        model = self.model_combo.currentData()
        aspect_ratio = self.aspect_combo.currentData()
        num_outputs = self.num_spin.value()

        seed = None
        seed_text = self.seed_input.text().strip()
        if seed_text:
            try:
                seed = int(seed_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid Seed",
                    "Seed must be a valid integer.",
                )
                return

        # Start generation
        self._set_generating(True)

        self.current_worker = GenerationWorker(
            api_key=self.config.api_key,
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            num_outputs=num_outputs,
            seed=seed,
        )

        self.current_worker.started.connect(self._on_generation_started)
        self.current_worker.progress.connect(self._on_generation_progress)
        self.current_worker.finished.connect(self._on_generation_finished)
        self.current_worker.error.connect(self._on_generation_error)

        self.worker_thread = run_worker(self.current_worker)

    def _set_generating(self, generating: bool) -> None:
        """Update UI for generation state."""
        self.generate_btn.setEnabled(not generating)
        self.progress_bar.setVisible(generating)
        if generating:
            self.progress_bar.setValue(0)
            self.status_label.setText("Starting...")
        else:
            self.status_label.setText("")

    @Slot()
    def _on_generation_started(self) -> None:
        """Handle generation started."""
        self.statusbar.showMessage("Generating...")

    @Slot(str, float)
    def _on_generation_progress(self, status: str, percentage: float) -> None:
        """Handle generation progress update."""
        self.progress_bar.setValue(int(percentage * 100))
        self.status_label.setText(status)

    @Slot(object)
    def _on_generation_finished(self, response: GenerateResponse) -> None:
        """Handle generation completion."""
        self._set_generating(False)
        self.statusbar.showMessage(
            f"Generated {len(response.images)} image(s) | "
            f"Credits: {response.credits_remaining:.2f}",
            5000,
        )

        # Update credit display
        self.credit_display.set_credits(response.credits_remaining)

        # Add images to gallery
        for image in response.images:
            card = self.gallery.add_image(
                url=str(image.url),
                seed=image.seed,
                dimensions=image.dimensions,
            )

            # Download image data
            self._download_image(str(image.url))

        # Store in history
        self.generation_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": self.prompt_input.get_text(),
            "model": self.model_combo.currentData(),
            "images": [str(img.url) for img in response.images],
        })

        # Cleanup thread
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
        self.current_worker = None

    @Slot(str, object)
    def _on_generation_error(self, message: str, exception: Exception) -> None:
        """Handle generation error."""
        self._set_generating(False)
        self.statusbar.showMessage("Generation failed", 5000)

        QMessageBox.critical(
            self,
            "Generation Failed",
            f"Failed to generate image:\n\n{message}",
        )

        # Cleanup
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
        self.current_worker = None

    def _download_image(self, url: str) -> None:
        """Download image data for display."""
        worker = ImageDownloadWorker(self.config.api_key, url)

        def on_finished(download_url: str, data: bytes) -> None:
            card = self.gallery.get_card(download_url)
            if card:
                card.set_image(data)

        worker.finished.connect(on_finished)

        thread = run_worker(worker)
        self.download_threads.append(thread)

        # Cleanup completed threads
        self.download_threads = [t for t in self.download_threads if t.isRunning()]

    @Slot(object)
    def _on_image_selected(self, card: ImageCard) -> None:
        """Handle image selection in gallery."""
        if card.image_data:
            self.preview_frame.setVisible(True)
            image = QImage()
            if image.loadFromData(card.image_data):
                pixmap = QPixmap.fromImage(image)
                scaled = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)

    def _clear_gallery(self) -> None:
        """Clear the image gallery."""
        self.gallery.clear()
        self.preview_frame.setVisible(False)
        self.preview_label.clear()

    def _save_all_images(self) -> None:
        """Save all images to a directory."""
        if not self.gallery.cards:
            QMessageBox.information(
                self,
                "No Images",
                "No images to save. Generate some images first!",
            )
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            str(Path.home() / "Pictures"),
        )

        if not directory:
            return

        save_dir = Path(directory)
        saved_count = 0

        for i, card in enumerate(self.gallery.cards, 1):
            if card.image_data:
                filename = f"pixeldojo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
                filepath = save_dir / filename
                filepath.write_bytes(card.image_data)
                saved_count += 1

        QMessageBox.information(
            self,
            "Images Saved",
            f"Saved {saved_count} image(s) to {directory}",
        )

    def _set_api_key(self) -> None:
        """Show dialog to set API key."""
        key, ok = QInputDialog.getText(
            self,
            "Set API Key",
            "Enter your PixelDojo API key:",
            QLineEdit.EchoMode.Password,
            self.config.api_key,
        )

        if ok and key:
            self.config.save_api_key(key)
            self.config = reload_config()
            QMessageBox.information(
                self,
                "API Key Saved",
                "Your API key has been saved securely.",
            )

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About PixelDojo Studio",
            f"<h2>PixelDojo Studio</h2>"
            f"<p>Version {__version__}</p>"
            f"<p>Professional AI Image Generation</p>"
            f"<p>Powered by Flux, Qwen, and WAN models</p>"
            f"<hr>"
            f"<p>Built with Python and PySide6</p>"
            f"<p><a href='https://pixeldojo.ai'>pixeldojo.ai</a></p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        # Cancel any running generation
        if self.current_worker:
            self.current_worker.cancel()

        # Wait for threads
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(3000)

        for thread in self.download_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)

        event.accept()
