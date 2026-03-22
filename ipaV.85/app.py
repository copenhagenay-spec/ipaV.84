"""Simple speech-to-text helpers."""

from __future__ import annotations

import json
import os
import time
from queue import Queue
from typing import Tuple


class MissingDependencyError(RuntimeError):
    pass


_model_cache: dict = {}


def _require_deps() -> Tuple[object, object]:
    try:
        import sounddevice as sd  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime environment specific
        raise MissingDependencyError(
            "Missing dependency: sounddevice. Install with: pip install sounddevice"
        ) from exc

    try:
        from vosk import Model, KaldiRecognizer  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime environment specific
        raise MissingDependencyError(
            "Missing dependency: vosk. Install with: pip install vosk"
        ) from exc

    return sd, (Model, KaldiRecognizer)


def _resolve_model_path(model_path: str) -> str:
    resolved_model_path = model_path
    if os.path.isdir(model_path):
        entries = [
            os.path.join(model_path, name)
            for name in os.listdir(model_path)
        ]
        subdirs = [p for p in entries if os.path.isdir(p)]
        if len(subdirs) == 1:
            resolved_model_path = subdirs[0]
    return resolved_model_path


def transcribe_mic(
    seconds: int = 5,
    model_path: str = "data/model/en",
    samplerate: int = 16000,
) -> str:
    """
    Record from the default microphone for `seconds` and return a transcript.

    Requires:
      - sounddevice
      - vosk
      - a Vosk model at `model_path`
    """
    if seconds <= 0:
        raise ValueError("seconds must be > 0")

    sd, (Model, KaldiRecognizer) = _require_deps()

    resolved = _resolve_model_path(model_path)
    if resolved not in _model_cache:
        try:
            _model_cache[resolved] = Model(resolved)
        except Exception as exc:
            raise MissingDependencyError(
                "Missing model files. Download a Vosk model and place it at: "
                f"{model_path}"
            ) from exc
    model = _model_cache[resolved]

    q: Queue[bytes] = Queue()

    def _callback(indata, frames, time_info, status):  # type: ignore[override]
        if status:
            pass
        q.put(bytes(indata))

    rec = KaldiRecognizer(model, samplerate)
    text_parts = []

    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=4000,
        dtype="int16",
        channels=1,
        callback=_callback,
    ):
        end_time = time.time() + seconds
        while time.time() < end_time:
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get("text"):
                    text_parts.append(res["text"])

        final = json.loads(rec.FinalResult())
        if final.get("text"):
            text_parts.append(final["text"])

    return " ".join(text_parts).strip()


def transcribe_mic_hold(
    stop_event,
    model_path: str = "data/model/en",
    samplerate: int = 16000,
) -> str:
    """
    Record from the default microphone until stop_event is set.

    Requires:
      - sounddevice
      - vosk
      - a Vosk model at `model_path`
    """
    sd, (Model, KaldiRecognizer) = _require_deps()

    resolved = _resolve_model_path(model_path)
    if resolved not in _model_cache:
        try:
            _model_cache[resolved] = Model(resolved)
        except Exception as exc:
            raise MissingDependencyError(
                "Missing model files. Download a Vosk model and place it at: "
                f"{model_path}"
            ) from exc
    model = _model_cache[resolved]

    q: Queue[bytes] = Queue()

    def _callback(indata, frames, time_info, status):  # type: ignore[override]
        if status:
            pass
        q.put(bytes(indata))

    rec = KaldiRecognizer(model, samplerate)
    text_parts = []

    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=4000,
        dtype="int16",
        channels=1,
        callback=_callback,
    ):
        while not stop_event.is_set():
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get("text"):
                    text_parts.append(res["text"])

        final = json.loads(rec.FinalResult())
        if final.get("text"):
            text_parts.append(final["text"])

    return " ".join(text_parts).strip()
