"""Main entry point for Interview Assistant."""

import sys
import threading
from typing import Optional

from PyQt6.QtWidgets import QApplication

from audio_capture import capture_chunk, flush_pending_capture, list_loopback_devices, set_paused
from gemini_client import GeminiClient
from ui.dialogs import DeviceSelectorDialog, TrayIcon
from ui.window import AssistantWindow
from utils.global_hotkeys import GlobalHotkeys


def _capture_loop(
    window: AssistantWindow,
    client: GeminiClient,
    device_holder: list,
) -> None:
    """Background thread for continuous audio capture and analysis."""
    print(f"[capture] Boucle démarrée (device={device_holder[0]})")
    was_paused = False
    while True:
        if window._paused:
            if not was_paused:
                set_paused(True)
                was_paused = True
            import time
            time.sleep(0.3)
            continue
        elif was_paused:
            set_paused(False)
            was_paused = False

        try:
            wav_bytes = capture_chunk(device_holder[0])

            if wav_bytes is None:
                continue

            print("[state] LISTENING → ANALYZING")
            window.set_analyzing()

            result = client.analyze_audio(wav_bytes)
            if result:
                print("[state] ANALYZING → ANSWER")
                window.answer_result_ready.emit(result)
            else:
                print("[state] ANALYZING → LISTENING (pas de question)")
                window.set_listening()

        except Exception as e:
            print(f"[error] {e}")
            window.set_listening()


def _on_regenerate(
    window: AssistantWindow,
    client: GeminiClient,
    device_holder: list,
) -> None:
    """Handle retry: capture fresh audio and re-analyze."""
    def _run():
        try:
            flush_pending_capture()
            wav_bytes = capture_chunk(device_holder[0])
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


def _on_settings(window: AssistantWindow, device_holder: list) -> None:
    """Open device selector dialog and update capture device."""
    was_paused = window._paused
    if not was_paused:
        window.toggle_pause()

    devices = list_loopback_devices()
    dialog = DeviceSelectorDialog(devices)
    if dialog.exec() != 0:
        device_holder[0] = dialog.selected_device_index
        print(f"[settings] Périphérique changé : index={device_holder[0]}")

    if not was_paused:
        window.toggle_pause()


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)

    # Device selection via GUI dialog
    devices = list_loopback_devices()
    dialog = DeviceSelectorDialog(devices)
    if dialog.exec() == 0:
        return 0
    device_holder = [dialog.selected_device_index]
    print(f"[init] Périphérique sélectionné : index={device_holder[0]}")

    # Gemini client
    try:
        client = GeminiClient()
        print("[init] Client Gemini initialisé")
    except ValueError as e:
        print(f"[error] {e}")
        return 1

    # Main overlay window
    window = AssistantWindow()

    # Connect retry to actual re-capture
    window.regenerate_requested.connect(
        lambda: _on_regenerate(window, client, device_holder)
    )

    # Connect settings button
    window.settings_requested.connect(
        lambda: _on_settings(window, device_holder)
    )

    window.show()
    print("[init] Fenêtre overlay affichée")

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
        args=(window, client, device_holder),
        daemon=True,
    )
    capture_thread.start()
    print("[init] Démarrage terminé — en écoute…")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
