"""PyQt6 floating window with screen capture exclusion."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from utils.win_api import hide_from_screen_capture


class AssistantWindow(QWidget):
    """Floating window that displays AI-suggested answers."""

    answer_ready = pyqtSignal(str)

    def __init__(self) -> None:
        """Initialize the assistant window."""
        super().__init__()
        self._build_ui()
        self.answer_ready.connect(self._show_answer)

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setWindowTitle("Interview Assistant")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(480, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self._status_label = QLabel("En écoute...")
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")

        self._answer_label = QLabel("")
        self._answer_label.setWordWrap(True)
        self._answer_label.setStyleSheet(
            "background: rgba(20,20,20,0.88); "
            "color: #f0f0f0; "
            "font-size: 14px; "
            "padding: 12px; "
            "border-radius: 8px;"
        )

        layout.addWidget(self._status_label)
        layout.addWidget(self._answer_label)
        self.setLayout(layout)

    def showEvent(self, event) -> None:  # noqa: N802
        """Apply screen capture exclusion when window is shown."""
        super().showEvent(event)
        hwnd = int(self.winId())
        hide_from_screen_capture(hwnd)

    def _show_answer(self, text: str) -> None:
        """Update the answer display (called via signal from background thread)."""
        self._status_label.setText("Réponse suggérée")
        self._answer_label.setText(text)
