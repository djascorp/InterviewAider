"""Audio capture module using WASAPI loopback via sounddevice."""

import io
import wave
from typing import Optional

import numpy as np
import sounddevice as sd

SAMPLERATE = 44100
CHANNELS = 2
CHUNK_SEC = 3
DTYPE = np.int16


def list_loopback_devices() -> list[dict]:
    """List all input devices (including loopback)."""
    devices = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            devices.append({"index": i, "name": d["name"], "channels": d["max_input_channels"]})
    return devices


def print_loopback_devices() -> None:
    """Print available loopback devices for user selection."""
    devices = list_loopback_devices()
    for d in devices:
        print(f"[{d['index']}] {d['name']} ({d['channels']} channels)")


def capture_chunk(device_index: Optional[int] = None) -> bytes:
    """Capture CHUNK_SEC seconds of system audio and return WAV bytes."""
    frames = SAMPLERATE * CHUNK_SEC
    audio = sd.rec(
        frames=frames,
        samplerate=SAMPLERATE,
        channels=CHANNELS,
        dtype=DTYPE,
        device=device_index,
        blocking=True,
    )
    return _encode_wav(audio)


def _encode_wav(pcm: np.ndarray) -> bytes:
    """Encode PCM audio to WAV format in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(SAMPLERATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()
