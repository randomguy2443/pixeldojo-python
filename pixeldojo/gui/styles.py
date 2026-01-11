"""
Modern stylesheet for PixelDojo GUI.

Inspired by modern design systems with support for dark mode.
"""

DARK_THEME = """
/* Main Application */
QMainWindow {
    background-color: #1a1a2e;
}

QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* Buttons */
QPushButton {
    background-color: #6c5ce7;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #8075e8;
}

QPushButton:pressed {
    background-color: #5b4cdb;
}

QPushButton:disabled {
    background-color: #4a4a5e;
    color: #888;
}

QPushButton#secondaryButton {
    background-color: #2d2d44;
    border: 1px solid #4a4a5e;
}

QPushButton#secondaryButton:hover {
    background-color: #3d3d54;
}

QPushButton#dangerButton {
    background-color: #e74c3c;
}

QPushButton#dangerButton:hover {
    background-color: #f15a4a;
}

/* Text Input */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2d2d44;
    border: 2px solid #4a4a5e;
    border-radius: 8px;
    padding: 10px;
    color: #eaeaea;
    selection-background-color: #6c5ce7;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #6c5ce7;
}

QTextEdit#promptInput {
    font-size: 14px;
    min-height: 80px;
}

/* Combo Box */
QComboBox {
    background-color: #2d2d44;
    border: 2px solid #4a4a5e;
    border-radius: 8px;
    padding: 8px 12px;
    min-width: 150px;
}

QComboBox:hover {
    border-color: #6c5ce7;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #6c5ce7;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d44;
    border: 2px solid #4a4a5e;
    border-radius: 8px;
    selection-background-color: #6c5ce7;
    padding: 5px;
}

/* Spin Box */
QSpinBox {
    background-color: #2d2d44;
    border: 2px solid #4a4a5e;
    border-radius: 8px;
    padding: 8px;
}

QSpinBox:focus {
    border-color: #6c5ce7;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #4a4a5e;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #6c5ce7;
}

/* Labels */
QLabel {
    color: #eaeaea;
    background-color: transparent;
}

QLabel#sectionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
    padding: 5px 0;
}

QLabel#subLabel {
    color: #888;
    font-size: 12px;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #2d2d44;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a5e;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6c5ce7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2d2d44;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #4a4a5e;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6c5ce7;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Progress Bar */
QProgressBar {
    background-color: #2d2d44;
    border: none;
    border-radius: 8px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #6c5ce7;
    border-radius: 8px;
}

/* Group Box */
QGroupBox {
    background-color: #2d2d44;
    border: 1px solid #4a4a5e;
    border-radius: 10px;
    margin-top: 15px;
    padding: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 10px;
    color: #6c5ce7;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #4a4a5e;
    border-radius: 8px;
    background-color: #2d2d44;
}

QTabBar::tab {
    background-color: #1a1a2e;
    border: 1px solid #4a4a5e;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #2d2d44;
    color: #6c5ce7;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #25253a;
}

/* Status Bar */
QStatusBar {
    background-color: #0f0f1a;
    color: #888;
    border-top: 1px solid #2d2d44;
}

QStatusBar::item {
    border: none;
}

/* Menu Bar */
QMenuBar {
    background-color: #0f0f1a;
    border-bottom: 1px solid #2d2d44;
    padding: 5px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 15px;
    border-radius: 5px;
}

QMenuBar::item:selected {
    background-color: #2d2d44;
}

QMenu {
    background-color: #2d2d44;
    border: 1px solid #4a4a5e;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    padding: 8px 30px;
    border-radius: 5px;
}

QMenu::item:selected {
    background-color: #6c5ce7;
}

QMenu::separator {
    height: 1px;
    background-color: #4a4a5e;
    margin: 5px 10px;
}

/* Dialog */
QDialog {
    background-color: #1a1a2e;
}

/* Message Box */
QMessageBox {
    background-color: #1a1a2e;
}

QMessageBox QLabel {
    color: #eaeaea;
}

/* Tool Tips */
QToolTip {
    background-color: #2d2d44;
    color: #eaeaea;
    border: 1px solid #6c5ce7;
    border-radius: 5px;
    padding: 5px 10px;
}

/* Frame */
QFrame#imageFrame {
    background-color: #2d2d44;
    border: 2px solid #4a4a5e;
    border-radius: 10px;
}

QFrame#imageFrame:hover {
    border-color: #6c5ce7;
}

/* Splitter */
QSplitter::handle {
    background-color: #4a4a5e;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #6c5ce7;
}
"""

LIGHT_THEME = """
/* Light theme - placeholder for future implementation */
QWidget {
    background-color: #f5f5f5;
    color: #333;
}
"""


def get_stylesheet(dark_mode: bool = True) -> str:
    """Get the application stylesheet."""
    return DARK_THEME if dark_mode else LIGHT_THEME
