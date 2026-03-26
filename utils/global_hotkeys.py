"""Global hotkey registration using Windows RegisterHotKey API."""

import ctypes
import ctypes.wintypes
import threading
from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal

# Virtual key codes
VK_SPACE = 0x20
VK_F9 = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A

# Modifier flags
MOD_CTRL = 0x0002
MOD_ALT = 0x0001
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312

_user32 = ctypes.windll.user32


class GlobalHotkeys(QObject):
    """Register and listen for global hotkeys via Windows API."""

    pause_triggered = pyqtSignal()
    collapse_triggered = pyqtSignal()
    toggle_visible_triggered = pyqtSignal()

    # Hotkey IDs
    _HOTKEY_PAUSE = 1       # Ctrl+Alt+Space
    _HOTKEY_COLLAPSE = 2    # Ctrl+Alt+H
    _HOTKEY_TOGGLE = 3      # Ctrl+Alt+V

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._running = False

    def start(self) -> None:
        """Start listening for global hotkeys in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop listening."""
        self._running = False

    def _listen(self) -> None:
        """Register hotkeys and pump messages in background thread."""
        _user32.RegisterHotKey(None, self._HOTKEY_PAUSE, MOD_CTRL | MOD_ALT | MOD_NOREPEAT, VK_SPACE)
        _user32.RegisterHotKey(None, self._HOTKEY_COLLAPSE, MOD_CTRL | MOD_ALT | MOD_NOREPEAT, ord('H'))
        _user32.RegisterHotKey(None, self._HOTKEY_TOGGLE, MOD_CTRL | MOD_ALT | MOD_NOREPEAT, ord('V'))

        msg = ctypes.wintypes.MSG()
        while self._running:
            if _user32.PeekMessageW(ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1):
                hotkey_id = msg.wParam
                if hotkey_id == self._HOTKEY_PAUSE:
                    self.pause_triggered.emit()
                elif hotkey_id == self._HOTKEY_COLLAPSE:
                    self.collapse_triggered.emit()
                elif hotkey_id == self._HOTKEY_TOGGLE:
                    self.toggle_visible_triggered.emit()
            else:
                import time
                time.sleep(0.05)

        _user32.UnregisterHotKey(None, self._HOTKEY_PAUSE)
        _user32.UnregisterHotKey(None, self._HOTKEY_COLLAPSE)
        _user32.UnregisterHotKey(None, self._HOTKEY_TOGGLE)
