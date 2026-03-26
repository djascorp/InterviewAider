"""Overlay widgets for the Interview Assistant."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QScrollArea,
    QApplication,
)
from PyQt6.QtGui import QCursor

from ui.overlay_styles import (
    COLORS,
    HEADER_STYLE,
    STATUS_DOT_STYLE,
    STATUS_DOT_PAUSED_STYLE,
    HEADER_TITLE_STYLE,
    HEADER_BTN_STYLE,
    WAVE_STRIP_STYLE,
    WAVE_BAR_STYLE,
    WAVE_META_STYLE,
    LISTENING_STYLE,
    LISTEN_LABEL_STYLE,
    LISTEN_SUB_STYLE,
    ANALYZING_STYLE,
    ANALYZING_DOT_STYLE,
    ANALYZING_LABEL_STYLE,
    QUESTION_STRIP_STYLE,
    QUESTION_TAG_STYLE,
    QUESTION_TEXT_STYLE,
    ANSWER_MAIN_STYLE,
    BULLET_STYLE,
    BULLET_DASH_STYLE,
    BULLET_TEXT_STYLE,
    ACTION_BAR_STYLE,
    ACTION_BTN_STYLE,
    LATENCY_STYLE,
    COLLAPSED_BODY_STYLE,
    COLLAPSED_TEXT_STYLE,
    SCROLLBAR_STYLE,
)


class StatusDot(QLabel):
    """Animated status indicator dot."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("statusDot")
        self.setFixedSize(7, 7)
        self._paused = False
        self._apply_style()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._opacity = 1.0
        self._direction = -1
        self._timer.start(30)

    def _apply_style(self):
        style = STATUS_DOT_PAUSED_STYLE if self._paused else STATUS_DOT_STYLE
        self.setStyleSheet(style)

    def _animate(self):
        if self._paused:
            return
        self._opacity += self._direction * 0.03
        if self._opacity <= 0.5:
            self._direction = 1
        elif self._opacity >= 1.0:
            self._direction = -1
        self.setStyleSheet(
            f"background: {COLORS['green']}; border-radius: 4px; opacity: {self._opacity};"
        )

    def set_paused(self, paused: bool):
        self._paused = paused
        if paused:
            self._apply_style()
        else:
            self._opacity = 1.0


class HeaderWidget(QWidget):
    """Header with status dot, title, and action buttons."""

    pause_clicked = pyqtSignal()
    collapse_clicked = pyqtSignal()
    hide_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(32)
        self.setStyleSheet(HEADER_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self.status_dot = StatusDot(self)
        layout.addWidget(self.status_dot)

        self.title_label = QLabel("InterviewAI · en écoute")
        self.title_label.setObjectName("headerTitle")
        self.title_label.setStyleSheet(HEADER_TITLE_STYLE)
        layout.addWidget(self.title_label, 1)

        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setObjectName("headerBtn")
        self.pause_btn.setStyleSheet(HEADER_BTN_STYLE)
        self.pause_btn.setFixedSize(22, 22)
        self.pause_btn.setToolTip("Pause (Espace)")
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        layout.addWidget(self.pause_btn)

        self.collapse_btn = QPushButton("−")
        self.collapse_btn.setObjectName("headerBtn")
        self.collapse_btn.setStyleSheet(HEADER_BTN_STYLE)
        self.collapse_btn.setFixedSize(22, 22)
        self.collapse_btn.setToolTip("Réduire")
        self.collapse_btn.clicked.connect(self.collapse_clicked.emit)
        layout.addWidget(self.collapse_btn)

        self.hide_btn = QPushButton("◻")
        self.hide_btn.setObjectName("headerBtn")
        self.hide_btn.setStyleSheet(HEADER_BTN_STYLE)
        self.hide_btn.setFixedSize(22, 22)
        self.hide_btn.setToolTip("Invisible (screen share)")
        self.hide_btn.clicked.connect(self.hide_clicked.emit)
        layout.addWidget(self.hide_btn)

    def set_title(self, text: str):
        self.title_label.setText(text)

    def set_paused(self, paused: bool):
        self.status_dot.set_paused(paused)
        self.pause_btn.setText("▶" if paused else "⏸")
        self.pause_btn.setToolTip("Reprendre (Espace)" if paused else "Pause (Espace)")


class WaveBar(QLabel):
    """Single animated waveform bar."""

    def __init__(self, duration: int = 800, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("waveBar")
        self.setStyleSheet(WAVE_BAR_STYLE)
        self.setFixedWidth(3)
        self._min_height = 3
        self._max_height = 18
        self._current = self._min_height
        self._direction = 1
        self._duration = duration
        self._paused = False
        self.setFixedHeight(self._min_height)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)

    def start(self):
        self._paused = False
        self._timer.start(30)

    def stop(self):
        self._paused = True
        self._timer.stop()
        self.setFixedHeight(self._min_height)
        self.setStyleSheet(f"background: rgba(168,224,99,0.15); border-radius: 1px;")

    def _animate(self):
        if self._paused:
            return

        step = (self._max_height - self._min_height) / (self._duration / 30)
        self._current += self._direction * step

        if self._current >= self._max_height:
            self._direction = -1
        elif self._current <= self._min_height:
            self._direction = 1

        self.setFixedHeight(int(self._current))
        self.setStyleSheet(WAVE_BAR_STYLE)


class WaveformStrip(QWidget):
    """Waveform visualization strip."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("waveStrip")
        self.setFixedHeight(32)
        self.setStyleSheet(WAVE_STRIP_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(2)

        self.bars: list[WaveBar] = []
        durations = [550, 800, 650, 1000, 700, 900, 600, 1100, 750, 850, 500, 950, 680, 1050, 720, 880, 580, 930]
        for d in durations:
            bar = WaveBar(d, self)
            bar.start()
            self.bars.append(bar)
            layout.addWidget(bar)

        layout.addStretch()

        self.meta_label = QLabel("WASAPI · 44.1k")
        self.meta_label.setObjectName("waveMeta")
        self.meta_label.setStyleSheet(WAVE_META_STYLE)
        layout.addWidget(self.meta_label)

    def set_active(self, active: bool):
        for bar in self.bars:
            if active:
                bar.start()
                bar.setStyleSheet(WAVE_BAR_STYLE)
            else:
                bar.stop()


class ListeningState(QWidget):
    """State widget when listening for questions."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("stateListening")
        self.setStyleSheet(LISTENING_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        self.icon_label = QLabel("🎧")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(
            f"border: 1.5px solid {COLORS['border2']}; border-radius: 18px; padding: 8px;"
        )
        self.icon_label.setFixedSize(36, 36)
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("En attente d'une question…")
        self.label.setStyleSheet(LISTEN_LABEL_STYLE)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.sub_label = QLabel("gemini-3-flash · prêt")
        self.sub_label.setStyleSheet(LISTEN_SUB_STYLE)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_paused(self, paused: bool):
        if paused:
            self.label.setText("En pause")
            self.sub_label.setText("Appuyer Espace pour reprendre")
        else:
            self.label.setText("En attente d'une question…")
            self.sub_label.setText("gemini-3-flash · prêt")


class AnalyzingState(QWidget):
    """State widget when analyzing audio."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("stateAnalyzing")
        self.setStyleSheet(ANALYZING_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(5)
        self.dots: list[QLabel] = []
        for i in range(3):
            dot = QLabel()
            dot.setObjectName("analyzingDot")
            dot.setStyleSheet(ANALYZING_DOT_STYLE)
            dot.setFixedSize(5, 5)
            self.dots.append(dot)
            dots_layout.addWidget(dot)
        layout.addLayout(dots_layout)

        self.label = QLabel("Analyse en cours…")
        self.label.setStyleSheet(ANALYZING_LABEL_STYLE)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._timer = QTimer(self)
        self._opacity = [0.2, 0.2, 0.2]
        self._phase = [0, 0.2, 0.4]
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)

    def _animate(self):
        for i, dot in enumerate(self.dots):
            self._phase[i] += 0.05
            if self._phase[i] > 1:
                self._phase[i] = 0
            opacity = 0.2 + 0.8 * (0.5 + 0.5 * abs(self._phase[i] - 0.5))
            dot.setStyleSheet(
                f"background: {COLORS['green']}; border-radius: 3px; opacity: {opacity};"
            )


class BulletWidget(QWidget):
    """Single bullet point widget."""

    def __init__(self, text: str, delay_ms: int = 0, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("bullet")
        self.setStyleSheet(BULLET_STYLE)
        self._build_ui(text, delay_ms)

    def _build_ui(self, text: str, delay_ms: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 6, 9, 6)
        layout.setSpacing(8)

        dash = QLabel("—")
        dash.setObjectName("bulletDash")
        dash.setStyleSheet(BULLET_DASH_STYLE)
        dash.setFixedWidth(10)
        layout.addWidget(dash)

        text_label = QLabel(text)
        text_label.setObjectName("bulletText")
        text_label.setStyleSheet(BULLET_TEXT_STYLE)
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)

        if delay_ms > 0:
            self.setGraphicsEffect(None)
            self.setStyleSheet(f"background: transparent; border: none;")
            QTimer.singleShot(delay_ms, lambda: self._show(text))

    def _show(self, text: str):
        self.setStyleSheet(BULLET_STYLE)


class AnswerState(QWidget):
    """State widget displaying the answer."""

    copy_clicked = pyqtSignal()
    regenerate_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("stateAnswer")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Question strip
        self.question_strip = QWidget()
        self.question_strip.setObjectName("questionStrip")
        self.question_strip.setStyleSheet(QUESTION_STRIP_STYLE)
        q_layout = QVBoxLayout(self.question_strip)
        q_layout.setContentsMargins(14, 10, 14, 10)
        q_layout.setSpacing(4)

        self.question_tag = QLabel("QUESTION DETECTEE")
        self.question_tag.setObjectName("questionTag")
        self.question_tag.setStyleSheet(QUESTION_TAG_STYLE)
        q_layout.addWidget(self.question_tag)

        self.question_text = QLabel("")
        self.question_text.setObjectName("questionText")
        self.question_text.setStyleSheet(QUESTION_TEXT_STYLE)
        self.question_text.setWordWrap(True)
        q_layout.addWidget(self.question_text)

        layout.addWidget(self.question_strip)

        # Answer body
        scroll = QScrollArea()
        scroll.setObjectName("answerBody")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(SCROLLBAR_STYLE)
        scroll.setMaximumHeight(260)

        self.answer_content = QWidget()
        self.answer_content.setStyleSheet("background: transparent;")
        a_layout = QVBoxLayout(self.answer_content)
        a_layout.setContentsMargins(14, 12, 14, 12)
        a_layout.setSpacing(12)

        self.answer_main = QLabel("")
        self.answer_main.setObjectName("answerMain")
        self.answer_main.setStyleSheet(ANSWER_MAIN_STYLE)
        self.answer_main.setWordWrap(True)
        a_layout.addWidget(self.answer_main)

        self.bullets_container = QWidget()
        self.bullets_layout = QVBoxLayout(self.bullets_container)
        self.bullets_layout.setContentsMargins(0, 0, 0, 0)
        self.bullets_layout.setSpacing(5)
        a_layout.addWidget(self.bullets_container)
        a_layout.addStretch()

        scroll.setWidget(self.answer_content)
        layout.addWidget(scroll)

        # Action bar
        self.action_bar = QWidget()
        self.action_bar.setObjectName("actionBar")
        self.action_bar.setStyleSheet(ACTION_BAR_STYLE)
        self.action_bar.setFixedHeight(36)
        ab_layout = QHBoxLayout(self.action_bar)
        ab_layout.setContentsMargins(10, 8, 10, 8)
        ab_layout.setSpacing(6)

        self.copy_btn = QPushButton("⎘ copier")
        self.copy_btn.setObjectName("actBtn")
        self.copy_btn.setStyleSheet(ACTION_BTN_STYLE)
        self.copy_btn.clicked.connect(self.copy_clicked.emit)
        ab_layout.addWidget(self.copy_btn)

        self.retry_btn = QPushButton("↻ retry")
        self.retry_btn.setObjectName("actBtn")
        self.retry_btn.setStyleSheet(ACTION_BTN_STYLE)
        self.retry_btn.clicked.connect(self.regenerate_clicked.emit)
        ab_layout.addWidget(self.retry_btn)

        ab_layout.addStretch()

        self.latency_label = QLabel("")
        self.latency_label.setObjectName("latency")
        self.latency_label.setStyleSheet(LATENCY_STYLE)
        ab_layout.addWidget(self.latency_label)

        layout.addWidget(self.action_bar)

    def set_content(self, question: str, answer: str, bullets: list[str], latency: str):
        self.question_text.setText(question)
        self.answer_main.setText(answer)
        self.latency_label.setText(f"<b>{latency}</b>")

        # Clear old bullets
        while self.bullets_layout.count():
            item = self.bullets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new bullets with staggered animation
        for i, bullet_text in enumerate(bullets):
            delay = 50 + i * 70
            bullet = BulletWidget(bullet_text, delay)
            self.bullets_layout.addWidget(bullet)

    def show_copy_feedback(self, success: bool = True):
        text = "✓ copié" if success else "✕ erreur"
        self.copy_btn.setText(text)
        if success:
            self.copy_btn.setStyleSheet(
                f"{ACTION_BTN_STYLE} color: {COLORS['green']};"
            )
        QTimer.singleShot(1500, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.copy_btn.setText("⎘ copier")
        self.copy_btn.setStyleSheet(ACTION_BTN_STYLE)


class CollapsedState(QWidget):
    """Collapsed mini view widget."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("collapsedBody")
        self.setStyleSheet(COLLAPSED_BODY_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.status_dot = StatusDot(self)
        layout.addWidget(self.status_dot)

        self.text_label = QLabel("En écoute…")
        self.text_label.setObjectName("collapsedText")
        self.text_label.setStyleSheet(COLLAPSED_TEXT_STYLE)
        layout.addWidget(self.text_label, 1)

    def set_text(self, text: str):
        self.text_label.setText(text)

    def set_paused(self, paused: bool):
        self.status_dot.set_paused(paused)
