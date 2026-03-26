"""PyQt6 floating overlay window with screen capture exclusion."""

from enum import Enum
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from ui.widgets import (
    HeaderWidget,
    WaveformStrip,
    ListeningState,
    AnalyzingState,
    AnswerState,
    CollapsedState,
)
from ui.overlay_styles import COLORS
from utils.win_api import hide_from_screen_capture


class OverlayState(Enum):
    LISTENING = "listening"
    ANALYZING = "analyzing"
    ANSWER = "answer"


class AssistantWindow(QWidget):
    """Floating overlay window that displays AI-suggested answers."""

    answer_ready = pyqtSignal(str)
    state_changed = pyqtSignal(OverlayState)
    copy_requested = pyqtSignal()
    regenerate_requested = pyqtSignal()
    analyzing_started = pyqtSignal()
    answer_result_ready = pyqtSignal(object)
    settings_requested = pyqtSignal()

    EXPANDED_WIDTH = 340
    COLLAPSED_WIDTH = 180

    def __init__(self) -> None:
        """Initialize the assistant window."""
        super().__init__()
        self._state = OverlayState.LISTENING
        self._paused = False
        self._collapsed = False
        self._hidden_from_capture = True
        self._positioned = False
        self._dragging = False
        self._drag_offset = QPoint()
        self._current_question: Optional[str] = None
        self._current_answer: Optional[str] = None
        self._current_bullets: list[str] = []
        self._current_latency: str = ""
        self._history: list[tuple[str, str, list[str], str]] = []
        self._history_index: int = -1

        self._build_ui()
        self._connect_signals()
        self.answer_ready.connect(self._show_answer)
        self.answer_result_ready.connect(self._on_result)

    def _build_ui(self) -> None:
        """Build the UI components."""
        self.setObjectName("overlay")
        self.setWindowTitle("Interview Assistant")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setMinimumHeight(100)
        self.setMaximumHeight(600)
        self.setStyleSheet(
            f"""
            QWidget#overlay {{
                background: {COLORS['bg_hex']};
                border: 1px solid {COLORS['border2']};
                border-radius: 14px;
            }}
            """
        )

        self._container = QWidget(self)
        self._container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = HeaderWidget(self)
        layout.addWidget(self._header)

        # Waveform strip
        self._waveform = WaveformStrip(self)
        layout.addWidget(self._waveform)

        # States
        self._listening_state = ListeningState(self)
        layout.addWidget(self._listening_state)

        self._analyzing_state = AnalyzingState(self)
        self._analyzing_state.hide()
        layout.addWidget(self._analyzing_state)

        self._answer_state = AnswerState(self)
        self._answer_state.hide()
        layout.addWidget(self._answer_state)

        # Collapsed state
        self._collapsed_state = CollapsedState(self)
        self._collapsed_state.hide()
        layout.addWidget(self._collapsed_state)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._container)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._header.pause_clicked.connect(self.toggle_pause)
        self._header.collapse_clicked.connect(self.toggle_collapse)
        self._header.hide_clicked.connect(self.toggle_screen_capture_visibility)
        self._header.settings_clicked.connect(self.settings_requested.emit)
        self._answer_state.copy_clicked.connect(self._copy_answer)
        self._answer_state.regenerate_clicked.connect(self._on_regenerate)
        self._answer_state.prev_clicked.connect(self.show_previous)
        self._answer_state.next_clicked.connect(self.show_next)

    def showEvent(self, event) -> None:  # noqa: N802
        """Apply screen capture exclusion when window is shown."""
        super().showEvent(event)
        self._apply_screen_capture_exclusion()
        self._apply_initial_hide_btn_style()

        if not self._positioned:
            self._positioned = True
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                x = geom.right() - self.width() - 20
                y = geom.top() + 60
                self.move(x, y)

    def _apply_initial_hide_btn_style(self) -> None:
        """Set hide button style based on initial _hidden_from_capture state."""
        if self._hidden_from_capture:
            self._header.hide_btn.setStyleSheet(
                f"background: {COLORS['green']}; border-radius: 5px; color: #0a0a0b;"
            )

    def _apply_screen_capture_exclusion(self) -> None:
        """Hide window from screen capture if needed."""
        if self._hidden_from_capture:
            hwnd = int(self.winId())
            hide_from_screen_capture(hwnd)

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self._paused = not self._paused
        print(f"[state] {'⏸ EN PAUSE' if self._paused else '▶ REPRISE écoute'}")
        self._header.set_paused(self._paused)
        self._waveform.set_active(not self._paused)
        self._listening_state.set_paused(self._paused)
        self._collapsed_state.set_paused(self._paused)

        if self._paused:
            self._header.set_title("<span style='color:#edeae4'>InterviewAI</span> · en pause")
        else:
            self._header.set_title("<span style='color:#edeae4'>InterviewAI</span> · en écoute")

    def toggle_collapse(self) -> None:
        """Toggle collapsed state with smooth animation."""
        self._collapsed = not self._collapsed

        if self._collapsed:
            target_width = self.COLLAPSED_WIDTH
            self._waveform.hide()
            self._listening_state.hide()
            self._analyzing_state.hide()
            self._answer_state.hide()
            self._collapsed_state.show()
            self._header.collapse_btn.setText("+")
        else:
            target_width = self.EXPANDED_WIDTH
            self._collapsed_state.hide()
            self._set_state(self._state)
            self._header.collapse_btn.setText("−")

        self.setMinimumWidth(min(self.width(), target_width))
        self.setMaximumWidth(max(self.width(), target_width))

        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(200)
        anim.setStartValue(self.width())
        anim.setEndValue(target_width)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim_min = QPropertyAnimation(self, b"minimumWidth")
        anim_min.setDuration(200)
        anim_min.setStartValue(self.width())
        anim_min.setEndValue(target_width)
        anim_min.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim.finished.connect(lambda: self._finalize_collapse(target_width))
        self._collapse_anim = anim
        self._collapse_anim_min = anim_min
        anim.start()
        anim_min.start()

    def _finalize_collapse(self, width: int) -> None:
        """Lock width after collapse animation finishes."""
        self.setFixedWidth(width)

    def toggle_screen_capture_visibility(self) -> None:
        """Toggle visibility in screen capture."""
        self._hidden_from_capture = not self._hidden_from_capture
        self._apply_screen_capture_exclusion()

        if self._hidden_from_capture:
            self._header.hide_btn.setStyleSheet(
                f"background: {COLORS['green']}; border-radius: 5px; color: #0a0a0b;"
            )
        else:
            self._header.hide_btn.setStyleSheet(
                "background: transparent; border: none; border-radius: 5px; "
                f"color: {COLORS['text3']};"
            )

    def _set_state(self, state: OverlayState) -> None:
        """Set the current overlay state."""
        self._state = state

        if self._collapsed:
            self._waveform.hide()
            self._listening_state.hide()
            self._analyzing_state.hide()
            self._answer_state.hide()
            return

        self._waveform.show()

        if state == OverlayState.LISTENING:
            self._listening_state.show()
            self._analyzing_state.hide()
            self._answer_state.hide()
            self._header.set_title("<span style='color:#edeae4'>InterviewAI</span> · en écoute")
        elif state == OverlayState.ANALYZING:
            self._listening_state.hide()
            self._analyzing_state.show()
            self._answer_state.hide()
            self._header.set_title("<span style='color:#edeae4'>InterviewAI</span> · analyse…")
        elif state == OverlayState.ANSWER:
            self._listening_state.hide()
            self._analyzing_state.hide()
            self._answer_state.show()
            self._header.set_title("<span style='color:#edeae4'>InterviewAI</span> · réponse prête")

        self.state_changed.emit(state)

    def set_listening(self) -> None:
        """Set overlay to listening state."""
        self._set_state(OverlayState.LISTENING)

    def set_analyzing(self) -> None:
        """Set overlay to analyzing state."""
        self._set_state(OverlayState.ANALYZING)
        self.analyzing_started.emit()

    def set_answer(self, question: str, answer: str, bullets: list[str], latency: str = "1.0s") -> None:
        """Set overlay to answer state with content."""
        self._current_question = question
        self._current_answer = answer
        self._current_bullets = bullets
        self._current_latency = latency
        self._history.append((question, answer, bullets, latency))
        self._history_index = len(self._history) - 1

        self._answer_state.set_content(question, answer, bullets, latency)
        self._collapsed_state.set_text(question[:30] + "…" if len(question) > 30 else question)
        self._set_state(OverlayState.ANSWER)

    def _show_answer(self, text: str) -> None:
        """Show answer from signal (compatibility with existing code)."""
        self.set_answer("Question détectée", text, [], "1.0s")

    def _on_result(self, result) -> None:
        """Handle structured AnalysisResult from Gemini."""
        self.set_answer(result.question, result.answer, result.bullets, result.latency)

    def _copy_answer(self) -> None:
        """Copy the current answer to clipboard."""
        if not self._current_question:
            return

        bullet_text = "\n".join(f"— {b}" for b in self._current_bullets)
        full_text = f"Q: {self._current_question}\n\nA: {self._current_answer}\n\n{bullet_text}"

        clipboard = QApplication.clipboard()
        clipboard.setText(full_text)

        self._answer_state.show_copy_feedback(success=True)
        self.copy_requested.emit()

    def _on_regenerate(self) -> None:
        """Handle regenerate request."""
        self.set_analyzing()
        self.regenerate_requested.emit()

    def show_previous(self) -> None:
        """Show previous answer from history."""
        if self._history_index > 0:
            self._history_index -= 1
            q, a, b, l = self._history[self._history_index]
            self._answer_state.set_content(q, a, b, l)
            self._header.set_title(f"<span style='color:#edeae4'>InterviewAI</span> · {self._history_index + 1}/{len(self._history)}")

    def show_next(self) -> None:
        """Show next answer from history."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            q, a, b, l = self._history[self._history_index]
            self._answer_state.set_content(q, a, b, l)
            self._header.set_title(f"<span style='color:#edeae4'>InterviewAI</span> · {self._history_index + 1}/{len(self._history)}")

    # Drag functionality
    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Start drag on header area."""
        if event.button() == Qt.MouseButton.LeftButton:
            header_rect = self._header.geometry()
            if header_rect.contains(event.position().toPoint()):
                self._dragging = True
                self._drag_offset = event.globalPosition().toPoint() - self.pos()
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        """Move window during drag."""
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            screen = QApplication.primaryScreen()
            if screen:
                screen_geom = screen.availableGeometry()
                new_x = max(0, min(new_pos.x(), screen_geom.width() - self.width()))
                new_y = max(0, min(new_pos.y(), screen_geom.height() - self.height()))
                self.move(new_x, new_y)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        """End drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Space:
            self.toggle_pause()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self._copy_answer()
            elif event.key() == Qt.Key.Key_R:
                self._on_regenerate()
            elif event.key() == Qt.Key.Key_H:
                self.toggle_collapse()
            elif event.key() == Qt.Key.Key_Left:
                self.show_previous()
            elif event.key() == Qt.Key.Key_Right:
                self.show_next()
