"""
PixelDojo GUI Application Entry Point.

Launch the PySide6-based desktop application.
"""

from __future__ import annotations

import os
import sys

# Ensure proper Qt platform on Linux
if sys.platform == "linux":
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")


def main() -> int:
    """
    Main entry point for the PixelDojo GUI application.

    Returns:
        Exit code (0 for success)
    """
    # Import here to defer Qt initialization
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from pixeldojo.gui.mainwindow import MainWindow
    from pixeldojo.gui.styles import get_stylesheet

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PixelDojo Studio")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PixelDojo")
    app.setOrganizationDomain("pixeldojo.ai")

    # Set default font
    font = QFont("Segoe UI", 10)
    if sys.platform == "linux":
        font = QFont("Ubuntu", 10)
    elif sys.platform == "darwin":
        font = QFont("SF Pro Display", 10)
    app.setFont(font)

    # Apply stylesheet
    app.setStyleSheet(get_stylesheet(dark_mode=True))

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
