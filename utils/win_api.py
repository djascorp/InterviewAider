"""Windows API utilities for screen capture exclusion."""

import ctypes

WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 build 2004+


def hide_from_screen_capture(hwnd: int) -> bool:
    """
    Make window invisible to screen recorders (Zoom, Teams, OBS, etc.).

    Args:
        hwnd: Window handle (HWND) as integer.

    Returns:
        True if successful, False otherwise.
    """
    result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    if not result:
        print("[warn] SetWindowDisplayAffinity failed - Windows version may be too old")
    return bool(result)
