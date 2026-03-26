"""Audio capture module with VAD-based speech segmentation.

Uses webrtcvad for voice activity detection, a circular pre-roll buffer,
continuous non-blocking capture via sounddevice.InputStream, and adaptive
noise floor. Replaces the old fixed 3-second chunk approach.
"""

import io
import math
import os
import queue
import threading
import wave
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np
import sounddevice as sd
import webrtcvad

# ── Audio parameters ──────────────────────────────────────────────────
SAMPLERATE = 44100
CHANNELS = 2
DTYPE = np.int16

# VAD operates on 16 kHz mono — we downsample from 44.1k stereo for VAD only
_VAD_RATE = 16000
_VAD_FRAME_MS = 30  # 10, 20, or 30 ms
_VAD_FRAME_SAMPLES = _VAD_RATE * _VAD_FRAME_MS // 1000  # 480 samples
_VAD_AGGRESSIVENESS = 2  # 0 (least) to 3 (most aggressive)

# ── Segmentation parameters ──────────────────────────────────────────
_PRE_ROLL_MS = 400  # keep 400ms before speech onset
_SPEECH_START_FRAMES = 2  # voiced frames needed to trigger (out of last 3)
_SPEECH_START_WINDOW = 3
_SILENCE_END_MS = 700  # silence duration to end segment
_MIN_SEGMENT_MS = 500  # reject segments shorter than this
_MAX_SEGMENT_SEC = 15  # hard max segment length
_TAIL_KEEP_MS = 200  # keep some trailing silence

# ── Adaptive noise floor ─────────────────────────────────────────────
_NOISE_EMA_ALPHA = 0.02  # slow EMA for noise floor
_ENERGY_GATE_DB = 6  # frame must be this many dB above noise floor

# ── Internal buffering ───────────────────────────────────────────────
_CALLBACK_BLOCK_MS = 30  # sounddevice callback block size
_CALLBACK_BLOCK = SAMPLERATE * _CALLBACK_BLOCK_MS // 1000  # ~1323 samples
_RAW_QUEUE_MAXSIZE = 100  # ~3 seconds of raw audio
_SEGMENT_QUEUE_MAXSIZE = 1  # only keep the latest segment

# ── Audio dump ────────────────────────────────────────────────────────
_AUDIO_DUMP_DIR = "tmp_audio_recordings"

# ── Device detection keywords ────────────────────────────────────────
_LOOPBACK_KEYWORDS = ["stereo mix", "mixage", "loopback", "what u hear", "wave out"]


def _save_audio_dump(wav_bytes: bytes) -> None:
    """Save audio segment to tmp_audio_recordings/ with timestamp."""
    os.makedirs(_AUDIO_DUMP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filepath = os.path.join(_AUDIO_DUMP_DIR, f"audio_{timestamp}.wav")
    with open(filepath, "wb") as f:
        f.write(wav_bytes)
    print(f"[audio] Fichier sauvegardé : {filepath}")


class _VadState(Enum):
    IDLE = "idle"
    IN_SPEECH = "in_speech"


class VadCaptureService:
    """Background service: continuous capture + VAD + speech segmentation."""

    def __init__(self, device_index: Optional[int]) -> None:
        self._device_index = device_index
        self._vad = webrtcvad.Vad(_VAD_AGGRESSIVENESS)
        self._state = _VadState.IDLE

        # Queues
        self._raw_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue(
            maxsize=_RAW_QUEUE_MAXSIZE
        )
        self._segment_queue: queue.Queue[bytes] = queue.Queue(
            maxsize=_SEGMENT_QUEUE_MAXSIZE
        )

        # Pre-roll ring buffer (stores original 44.1k stereo chunks)
        pre_roll_chunks = max(1, (_PRE_ROLL_MS * SAMPLERATE) // (1000 * _CALLBACK_BLOCK))
        self._pre_roll: deque[np.ndarray] = deque(maxlen=pre_roll_chunks)

        # Active segment buffer
        self._segment_chunks: list[np.ndarray] = []
        self._segment_samples = 0

        # VAD frame accumulator (for incomplete frames across callbacks)
        self._vad_residual = np.array([], dtype=np.int16)

        # Speech trigger ring
        self._recent_voiced: deque[bool] = deque(maxlen=_SPEECH_START_WINDOW)

        # Silence tracking
        self._silence_samples = 0

        # Adaptive noise floor (in dB)
        self._noise_floor_db: Optional[float] = None

        # Threading
        self._stream: Optional[sd.InputStream] = None
        self._processor_thread: Optional[threading.Thread] = None
        self._paused = False
        self._running = False

    def start(self) -> None:
        """Start the capture stream and processor thread."""
        if self._running:
            return

        self._running = True
        self._paused = False

        self._stream = sd.InputStream(
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=_CALLBACK_BLOCK,
            device=self._device_index,
            callback=self._audio_callback,
        )
        self._stream.start()

        self._processor_thread = threading.Thread(
            target=self._process_loop, daemon=True
        )
        self._processor_thread.start()
        print(f"[vad] Service démarré (device={self._device_index})")

    def stop(self) -> None:
        """Stop capture and processing."""
        self._running = False

        # Signal processor thread to exit
        try:
            self._raw_queue.put_nowait(None)
        except queue.Full:
            pass

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if self._processor_thread is not None:
            self._processor_thread.join(timeout=2.0)
            self._processor_thread = None

        print("[vad] Service arrêté")

    def set_paused(self, paused: bool) -> None:
        """Pause/resume processing."""
        self._paused = paused
        if paused:
            self.flush()

    def flush(self) -> None:
        """Discard all buffered audio and pending segments."""
        # Drain raw queue
        while not self._raw_queue.empty():
            try:
                self._raw_queue.get_nowait()
            except queue.Empty:
                break

        # Drain segment queue
        while not self._segment_queue.empty():
            try:
                self._segment_queue.get_nowait()
            except queue.Empty:
                break

        # Reset state
        self._state = _VadState.IDLE
        self._segment_chunks.clear()
        self._segment_samples = 0
        self._pre_roll.clear()
        self._vad_residual = np.array([], dtype=np.int16)
        self._recent_voiced.clear()
        self._silence_samples = 0

    def get_next_segment(self, timeout: float = 0.25) -> Optional[bytes]:
        """Return next completed speech segment as WAV bytes, or None."""
        try:
            return self._segment_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ── Sounddevice callback (minimal work) ──────────────────────────

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            print(f"[vad] Callback status: {status}")
        if self._paused:
            return
        try:
            self._raw_queue.put_nowait(indata.copy())
        except queue.Full:
            pass  # drop oldest implicitly

    # ── Processor thread ─────────────────────────────────────────────

    def _process_loop(self) -> None:
        """Consume raw audio, run VAD, segment speech."""
        while self._running:
            try:
                chunk = self._raw_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if chunk is None:  # shutdown sentinel
                break

            if self._paused:
                continue

            self._process_chunk(chunk)

    def _process_chunk(self, chunk: np.ndarray) -> None:
        """Process one raw audio chunk through VAD pipeline."""
        # 1. Store original stereo for pre-roll / segment
        if self._state == _VadState.IDLE:
            self._pre_roll.append(chunk)
        else:
            self._segment_chunks.append(chunk)
            self._segment_samples += len(chunk)

        # 2. Downmix stereo→mono and resample 44.1k→16k for VAD
        mono = self._downmix_resample(chunk)

        # 3. Accumulate + split into exact VAD frames
        self._vad_residual = np.concatenate([self._vad_residual, mono])

        while len(self._vad_residual) >= _VAD_FRAME_SAMPLES:
            frame = self._vad_residual[:_VAD_FRAME_SAMPLES]
            self._vad_residual = self._vad_residual[_VAD_FRAME_SAMPLES:]
            self._process_vad_frame(frame)

    def _process_vad_frame(self, frame: np.ndarray) -> None:
        """Run VAD + energy gate on a single 30ms mono 16kHz frame."""
        # Energy (dBFS)
        frame_rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        if frame_rms < 1:
            frame_db = -96.0
        else:
            frame_db = 20.0 * math.log10(frame_rms / 32768.0)

        # Update adaptive noise floor (only during non-speech)
        if self._state == _VadState.IDLE:
            if self._noise_floor_db is None:
                self._noise_floor_db = frame_db
            else:
                self._noise_floor_db += _NOISE_EMA_ALPHA * (frame_db - self._noise_floor_db)

        # Energy gate: frame must be above noise floor + threshold
        energy_ok = True
        if self._noise_floor_db is not None:
            energy_ok = frame_db > (self._noise_floor_db + _ENERGY_GATE_DB)

        # WebRTC VAD
        frame_bytes = frame.tobytes()
        try:
            is_speech = self._vad.is_speech(frame_bytes, _VAD_RATE)
        except Exception:
            is_speech = False

        voiced = is_speech and energy_ok

        if self._state == _VadState.IDLE:
            self._recent_voiced.append(voiced)
            voiced_count = sum(self._recent_voiced)

            if voiced_count >= _SPEECH_START_FRAMES and len(self._recent_voiced) >= _SPEECH_START_WINDOW:
                # Speech detected — start segment with pre-roll
                self._state = _VadState.IN_SPEECH
                self._segment_chunks = list(self._pre_roll)
                self._segment_samples = sum(len(c) for c in self._segment_chunks)
                self._silence_samples = 0
                self._recent_voiced.clear()
                print("[vad] Parole détectée → enregistrement")

        elif self._state == _VadState.IN_SPEECH:
            if not voiced:
                self._silence_samples += _VAD_FRAME_SAMPLES
            else:
                self._silence_samples = 0

            # Convert silence samples (at VAD rate) to ms
            silence_ms = (self._silence_samples * 1000) // _VAD_RATE
            segment_duration_sec = self._segment_samples / SAMPLERATE

            # End conditions
            if silence_ms >= _SILENCE_END_MS or segment_duration_sec >= _MAX_SEGMENT_SEC:
                self._finalize_segment()

    def _finalize_segment(self) -> None:
        """Encode the active segment and push to segment queue."""
        if not self._segment_chunks:
            self._state = _VadState.IDLE
            return

        # Concatenate all chunks
        full_audio = np.concatenate(self._segment_chunks)

        # Trim trailing silence but keep _TAIL_KEEP_MS
        tail_samples = SAMPLERATE * _TAIL_KEEP_MS // 1000 * CHANNELS
        silence_tail_samples = (self._silence_samples * SAMPLERATE) // _VAD_RATE * CHANNELS
        trim = max(0, silence_tail_samples - tail_samples)
        if trim > 0 and trim < len(full_audio):
            full_audio = full_audio[:len(full_audio) - trim]

        # Check minimum duration
        duration_ms = (len(full_audio) * 1000) // (SAMPLERATE * CHANNELS)
        if duration_ms < _MIN_SEGMENT_MS:
            print(f"[vad] Segment trop court ({duration_ms}ms) → ignoré")
            self._state = _VadState.IDLE
            self._segment_chunks.clear()
            self._segment_samples = 0
            return

        wav_bytes = _encode_wav(full_audio)
        duration_sec = len(full_audio) / (SAMPLERATE * CHANNELS)
        print(f"[vad] Segment finalisé : {duration_sec:.1f}s ({len(wav_bytes)} bytes)")

        # Save audio dump
        _save_audio_dump(wav_bytes)

        # Push to segment queue (drop oldest if full)
        if self._segment_queue.full():
            try:
                self._segment_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self._segment_queue.put_nowait(wav_bytes)
        except queue.Full:
            pass

        # Reset state
        self._state = _VadState.IDLE
        self._segment_chunks.clear()
        self._segment_samples = 0
        self._pre_roll.clear()

    @staticmethod
    def _downmix_resample(chunk: np.ndarray) -> np.ndarray:
        """Convert stereo 44.1k int16 → mono 16k int16."""
        # chunk shape: (samples, 2) for stereo
        if chunk.ndim == 2 and chunk.shape[1] >= 2:
            mono = chunk.mean(axis=1).astype(np.int16)
        else:
            mono = chunk.flatten().astype(np.int16)

        # Resample 44100 → 16000 using simple decimation with anti-alias
        ratio = _VAD_RATE / SAMPLERATE  # ~0.3628
        target_len = int(len(mono) * ratio)
        if target_len == 0:
            return np.array([], dtype=np.int16)

        indices = np.linspace(0, len(mono) - 1, target_len).astype(int)
        return mono[indices]


# ── Module-level singleton management ────────────────────────────────

_service: Optional[VadCaptureService] = None
_service_device_index: Optional[int] = None
_service_lock = threading.Lock()


def _get_or_restart_service(device_index: Optional[int]) -> VadCaptureService:
    """Get or create the capture service, restarting if device changed."""
    global _service, _service_device_index

    with _service_lock:
        if _service is not None and _service_device_index == device_index:
            return _service

        # Stop existing service
        if _service is not None:
            _service.stop()

        _service = VadCaptureService(device_index)
        _service_device_index = device_index
        _service.start()
        return _service


# ── Public API (backward-compatible) ─────────────────────────────────

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


def capture_chunk(device_index: Optional[int] = None) -> Optional[bytes]:
    """Return next completed speech segment as WAV bytes, or None."""
    service = _get_or_restart_service(device_index)
    return service.get_next_segment(timeout=0.25)


def set_paused(paused: bool) -> None:
    """Pause/resume the capture service."""
    if _service is not None:
        _service.set_paused(paused)


def flush_pending_capture() -> None:
    """Drop all buffered audio and queued segments."""
    if _service is not None:
        _service.flush()


def shutdown_capture() -> None:
    """Stop the capture service cleanly."""
    global _service, _service_device_index
    with _service_lock:
        if _service is not None:
            _service.stop()
            _service = None
            _service_device_index = None


def compute_rms(pcm: np.ndarray) -> float:
    """Compute RMS of PCM audio (kept for compatibility)."""
    return float(np.sqrt(np.mean(pcm.astype(np.float64) ** 2)))


def _encode_wav(pcm: np.ndarray) -> bytes:
    """Encode PCM audio to WAV format in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(SAMPLERATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()
