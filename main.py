"""Main entry point for Interview Assistant."""

import sys
import threading
from typing import Optional

from PyQt6.QtWidgets import QApplication

from audio_capture import capture_chunk, list_loopback_devices
from gemini_client import GeminiClient
from ui.dialogs import DeviceSelectorDialog, TrayIcon
from ui.window import AssistantWindow
from utils.global_hotkeys import GlobalHotkeys


def _capture_loop(
    window: AssistantWindow,
    client: GeminiClient,
    device_index: Optional[int],
) -> None:
    """Background thread for continuous audio capture and analysis."""
    while True:
        if window._paused:
            import time
            time.sleep(0.3)
            continue

        try:
            wav_bytes = capture_chunk(device_index)

            if wav_bytes is None:
                continue

            window.set_analyzing()

            result = client.analyze_audio(wav_bytes)
            if result:
                window.answer_result_ready.emit(result)
            else:
                window.set_listening()

        except Exception as e:
            print(f"[error] {e}")
            window.set_listening()


def _on_regenerate(
    window: AssistantWindow,
    client: GeminiClient,
    device_index: Optional[int],
) -> None:
    """Handle retry: capture fresh audio and re-analyze."""
    def _run():
        try:
            wav_bytes = capture_chunk(device_index)
            if wav_bytes is None:
                window.set_listening()
                return
            result = client.analyze_audio(wav_bytes)
            if result:
                window.answer_result_ready.emit(result)
            else:
                window.set_listening()
        except Exception as e:
            print(f"[error] {e}")
            window.set_listening()

    threading.Thread(target=_run, daemon=True).start()


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)

    # Device selection via GUI dialog
    devices = list_loopback_devices()
    dialog = DeviceSelectorDialog(devices)
    if dialog.exec() == 0:
        return 0
    device_index = dialog.selected_device_index

    # Gemini client
    try:
        client = GeminiClient()
    except ValueError as e:
        print(f"[error] {e}")
        return 1

    # Main overlay window
    window = AssistantWindow()

    # Connect retry to actual re-capture
    window.regenerate_requested.connect(
        lambda: _on_regenerate(window, client, device_index)
    )

    window.show()

    # System tray icon
    tray = TrayIcon(window)
    tray.show()

    # Global hotkeys (Ctrl+Alt+Space, Ctrl+Alt+H, Ctrl+Alt+V)
    hotkeys = GlobalHotkeys()
    hotkeys.pause_triggered.connect(window.toggle_pause)
    hotkeys.collapse_triggered.connect(window.toggle_collapse)
    hotkeys.toggle_visible_triggered.connect(
        lambda: window.hide() if window.isVisible() else (window.show(), window.raise_())
    )
    hotkeys.start()

    # Audio capture thread
    capture_thread = threading.Thread(
        target=_capture_loop,
        args=(window, client, device_index),
        daemon=True,
    )
    capture_thread.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
