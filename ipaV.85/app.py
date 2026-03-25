"""Simple speech-to-text helpers — powered by faster-whisper."""

from __future__ import annotations

import os
import time
import numpy as np
from queue import Queue


class MissingDependencyError(RuntimeError):
    pass


_model_cache: dict = {}
_WHISPER_MODEL_SIZE = "base"  # tiny / base / small / medium — base is the sweet spot


def _require_sd():
    try:
        import sounddevice as sd  # type: ignore
        return sd
    except Exception as exc:
        raise MissingDependencyError(
            "Missing dependency: sounddevice. Install with: pip install sounddevice"
        ) from exc


def _get_whisper_model():
    """Lazy-load and cache the faster-whisper model."""
    if _WHISPER_MODEL_SIZE not in _model_cache:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as exc:
            raise MissingDependencyError(
                "Missing dependency: faster-whisper. Install with: pip install faster-whisper"
            ) from exc
        # cpu + int8 works well on most machines without a GPU
        _model_cache[_WHISPER_MODEL_SIZE] = WhisperModel(
            _WHISPER_MODEL_SIZE, device="cpu", compute_type="int8"
        )
    return _model_cache[_WHISPER_MODEL_SIZE]


def _record_audio(seconds: int, samplerate: int = 16000) -> np.ndarray:
    """Record `seconds` of audio and return as a float32 numpy array."""
    sd = _require_sd()
    q: Queue = Queue()

    def _callback(indata, frames, time_info, status):
        q.put(indata.copy())

    chunks = []
    with sd.InputStream(samplerate=samplerate, channels=1, dtype="float32", callback=_callback):
        end_time = time.time() + seconds
        while time.time() < end_time:
            chunks.append(q.get())

    return np.concatenate(chunks, axis=0).flatten()


def _record_audio_hold(stop_event, samplerate: int = 16000) -> np.ndarray:
    """Record audio until stop_event is set."""
    sd = _require_sd()
    q: Queue = Queue()

    def _callback(indata, frames, time_info, status):
        q.put(indata.copy())

    chunks = []
    with sd.InputStream(samplerate=samplerate, channels=1, dtype="float32", callback=_callback):
        while not stop_event.is_set():
            try:
                chunks.append(q.get(timeout=0.1))
            except Exception:
                continue

    if not chunks:
        return np.zeros(0, dtype="float32")
    return np.concatenate(chunks, axis=0).flatten()


def _transcribe_audio(audio: np.ndarray, samplerate: int = 16000) -> str:
    """Run faster-whisper on a float32 audio array and return transcript."""
    if audio.size == 0:
        return ""
    model = _get_whisper_model()
    segments, _ = model.transcribe(audio, language="en", beam_size=1, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


def transcribe_mic(
    seconds: int = 5,
    model_path: str = "",   # unused — kept for API compatibility
    samplerate: int = 16000,
) -> str:
    """Record for `seconds` and return a transcript via faster-whisper."""
    if seconds <= 0:
        raise ValueError("seconds must be > 0")
    audio = _record_audio(seconds, samplerate)
    return _transcribe_audio(audio, samplerate)


def transcribe_mic_hold(
    stop_event,
    model_path: str = "",   # unused — kept for API compatibility
    samplerate: int = 16000,
) -> str:
    """Record until stop_event is set and return a transcript via faster-whisper."""
    audio = _record_audio_hold(stop_event, samplerate)
    return _transcribe_audio(audio, samplerate)
