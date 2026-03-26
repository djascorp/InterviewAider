"""Audio capture module using WASAPI loopback via sounddevice."""

import io
import os
import wave
from datetime import datetime
from typing import Optional

import numpy as np
import sounddevice as sd

SAMPLERATE = 44100
CHANNELS = 2
CHUNK_SEC = 3
DTYPE = np.int16
RMS_THRESHOLD = 200

# Dossier temporaire pour sauvegarder les fichiers audio
_AUDIO_DUMP_DIR = "tmp_audio_recordings"
_LOOPBACK_KEYWORDS = ["stereo mix", "mixage", "loopback", "what u hear", "wave out"]


def list_loopback_devices() -> list[dict]:
    """List all input devices, flagging likely loopback/stereo-mix ones."""
    devices = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            name = d["name"]
            is_loopback = any(kw in name.lower() for kw in _LOOPBACK_KEYWORDS)
            devices.append({
                "index": i,
                "name": name,
                "channels": d["max_input_channels"],
                "is_loopback": is_loopback,
                "host_api": sd.query_hostapis(d["hostapi"])["name"],
            })
    return devices


def print_loopback_devices() -> None:
    """Print available loopback devices for user selection."""
    devices = list_loopback_devices()
    for d in devices:
        print(f"[{d['index']}] {d['name']} ({d['channels']} channels)")


def compute_rms(pcm: np.ndarray) -> float:
    return float(np.sqrt(np.mean(pcm.astype(np.float64) ** 2)))


def _ensure_audio_dump_dir() -> None:
    """Crée le dossier temporaire s'il n'existe pas."""
    if not os.path.exists(_AUDIO_DUMP_DIR):
        os.makedirs(_AUDIO_DUMP_DIR)
        print(f"[audio] Dossier créé : {_AUDIO_DUMP_DIR}")


def _save_audio_dump(wav_bytes: bytes) -> str:
    """Sauvegarde le fichier audio avec un timestamp."""
    _ensure_audio_dump_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"audio_{timestamp}.wav"
    filepath = os.path.join(_AUDIO_DUMP_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(wav_bytes)
    print(f"[audio] Fichier sauvegardé : {filepath}")
    return filepath


def capture_chunk(device_index: Optional[int] = None) -> Optional[bytes]:
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
    rms = compute_rms(audio)
    if rms < RMS_THRESHOLD:
        print(f"[audio] RMS={rms:.0f} (seuil={RMS_THRESHOLD}) → silence, ignoré")
        return None
    print(f"[audio] RMS={rms:.0f} (seuil={RMS_THRESHOLD}) → audio détecté, envoi à Gemini")
    wav_bytes = _encode_wav(audio)
    _save_audio_dump(wav_bytes)
    return wav_bytes


def _encode_wav(pcm: np.ndarray) -> bytes:
    """Encode PCM audio to WAV format in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(SAMPLERATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()
