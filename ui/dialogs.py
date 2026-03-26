"""Dialogs for the Interview Assistant."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
)

from ui.overlay_styles import COLORS, FONTS


class DeviceSelectorDialog(QDialog):
    """Dialog for selecting an audio input device."""

    def __init__(self, devices: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interview Assistant — Audio Device")
        self.setFixedSize(520, 220)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_hex']};
                border: 1px solid {COLORS['border2']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {COLORS['text']};
                font-family: {FONTS['sans']};
            }}
            QComboBox {{
                background: {COLORS['bg3']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border2']};
                border-radius: 6px;
                padding: 6px 10px;
                font-family: {FONTS['mono']};
                font-size: 11px;
                min-height: 28px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_hex']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border2']};
                selection-background-color: {COLORS['bg3']};
            }}
        """)

        self._selected_index = None
        self._devices = devices
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🎧 Sélectionner le périphérique audio")
        title.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {COLORS['text']};")
        layout.addWidget(title)

        subtitle = QLabel("Choisissez le device loopback (Stereo Mix, WASAPI…)")
        subtitle.setStyleSheet(f"font-size: 11px; color: {COLORS['text2']};")
        layout.addWidget(subtitle)

        self._combo = QComboBox()
        first_loopback_idx = -1
        for i, d in enumerate(self._devices):
            is_lb = d.get("is_loopback", False)
            host = d.get("host_api", "")
            tag = " ★ LOOPBACK" if is_lb else ""
            label = f"[{d['index']}] {d['name']} ({d['channels']}ch · {host}){tag}"
            self._combo.addItem(label, d["index"])
            if is_lb and first_loopback_idx == -1:
                first_loopback_idx = i
        if first_loopback_idx >= 0:
            self._combo.setCurrentIndex(first_loopback_idx)
        layout.addWidget(self._combo)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        default_btn = QPushButton("Défaut")
        default_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                color: {COLORS['text2']};
                font-family: {FONTS['mono']};
                font-size: 11px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg3']};
                color: {COLORS['text']};
            }}
        """)
        default_btn.clicked.connect(self._use_default)
        btn_layout.addWidget(default_btn)

        ok_btn = QPushButton("Confirmer")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['green']};
                border: none;
                border-radius: 6px;
                color: #0a0a0b;
                font-family: {FONTS['mono']};
                font-size: 11px;
                font-weight: 500;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: #b8ee72;
            }}
        """)
        ok_btn.clicked.connect(self._confirm)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _use_default(self):
        self._selected_index = None
        self.accept()

    def _confirm(self):
        self._selected_index = self._combo.currentData()
        self.accept()

    @property
    def selected_device_index(self):
        return self._selected_index


class TrayIcon(QSystemTrayIcon):
    """System tray icon for Interview Assistant."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self._window = window
        self.setIcon(self._create_icon())
        self.setToolTip("Interview Assistant")
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _create_icon(self):
        """Create a simple green dot icon programmatically."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS['green']))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        return QIcon(pixmap)

    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background: {COLORS['bg_hex']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border2']};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 4px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {COLORS['bg3']};
            }}
        """)

        show_action = menu.addAction("Afficher / Masquer")
        show_action.triggered.connect(self._toggle_window)

        pause_action = menu.addAction("Pause / Reprendre")
        pause_action.triggered.connect(self._window.toggle_pause)

        menu.addSeparator()

        quit_action = menu.addAction("Quitter")
        quit_action.triggered.connect(self._quit)

        self.setContextMenu(menu)

    def _toggle_window(self):
        if self._window.isVisible():
            self._window.hide()
        else:
            self._window.show()
            self._window.raise_()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _quit(self):
        QApplication.quit()
