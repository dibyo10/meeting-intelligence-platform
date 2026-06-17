"""Speech-to-text using faster-whisper (Whisper) with word-level timestamps.

The model is loaded lazily and cached, so importing this module is cheap and the API
server boots even before the (heavy) Whisper weights are downloaded.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..config import get_settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        s = get_settings()
        logger.info(
            "Loading Whisper model=%s device=%s compute=%s",
            s.whisper_model, s.whisper_device, s.whisper_compute_type,
        )
        _model = WhisperModel(
            s.whisper_model,
            device=s.whisper_device,
            compute_type=s.whisper_compute_type,
        )
    return _model


def transcribe(wav_path: Path) -> dict[str, Any]:
    """Transcribe a 16 kHz mono WAV.

    Returns ``{language, duration, segments:[{start,end,text,words:[...]}]}``.
    `vad_filter` trims silence/noise, which improves robustness and reduces
    hallucinated text on noisy recordings.
    """
    model = _get_model()
    segments_iter, info = model.transcribe(
        str(wav_path),
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )

    segments: list[dict[str, Any]] = []
    for seg in segments_iter:
        words = [
            {"start": float(w.start), "end": float(w.end), "word": w.word}
            for w in (seg.words or [])
            if w.start is not None and w.end is not None
        ]
        text = seg.text.strip()
        if not text:
            continue
        segments.append(
            {"start": float(seg.start), "end": float(seg.end), "text": text, "words": words}
        )

    return {
        "language": getattr(info, "language", None),
        "duration": float(getattr(info, "duration", 0.0) or 0.0),
        "segments": segments,
    }
