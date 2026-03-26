"""Main entry point for Interview Assistant."""

import sys
import threading
from typing import Optional

from PyQt6.QtWidgets import QApplication

from audio_capture import capture_chunk, print_loopback_devices
from gemini_client import GeminiClient
from ui.window import AssistantWindow


def _select_device() -> Optional[int]:
    """Prompt user to select an audio device."""
    print("\nAvailable audio input devices:")
    print_loopback_devices()
    print("\nEnter device index (or press Enter for default): ", end="")

    try:
        choice = input().strip()
        return int(choice) if choice else None
    except ValueError:
        print("Invalid input, using default device.")
        return None


def _capture_loop(window: AssistantWindow, client: GeminiClient, device_index: Optional[int]) -> None:
    """Background thread for continuous audio capture and analysis."""
    while True:
        try:
            wav_bytes = capture_chunk(device_index)
            reply = client.analyze_audio(wav_bytes)
            if reply:
                window.answer_ready.emit(reply)
        except Exception as e:
            print(f"[error] {e}")


def main() -> int:
    """Application entry point."""
    device_index = _select_device()

    try:
        client = GeminiClient()
    except ValueError as e:
        print(f"[error] {e}")
        return 1

    app = QApplication(sys.argv)
    window = AssistantWindow()
    window.show()

    capture_thread = threading.Thread(
        target=_capture_loop,
        args=(window, client, device_index),
        daemon=True,
    )
    capture_thread.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
