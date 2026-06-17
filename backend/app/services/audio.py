"""Audio utilities: normalise any upload to 16 kHz mono WAV and measure duration.

Primary path uses **PyAV**, which bundles its own ffmpeg libraries and therefore does not
depend on a working system `ffmpeg` binary. A subprocess `ffmpeg` call is kept as a
fallback for any exotic container PyAV can't open (only used if ffmpeg is available).

Both Whisper and pyannote are fed the same normalised WAV so their timestamps line up.
"""
from __future__ import annotations

import logging
import subprocess
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

TARGET_RATE = 16000


def _ensure_wav_pyav(src: Path, dst: Path) -> Path:
    import av
    import numpy as np

    dst.parent.mkdir(parents=True, exist_ok=True)
    container = av.open(str(src))
    try:
        stream = next(s for s in container.streams if s.type == "audio")
    except StopIteration:
        container.close()
        raise RuntimeError("No audio stream found in input")

    resampler = av.AudioResampler(format="s16", layout="mono", rate=TARGET_RATE)
    chunks: list = []
    for frame in container.decode(stream):
        for rframe in resampler.resample(frame):
            chunks.append(rframe.to_ndarray())
    for rframe in resampler.resample(None):  # flush
        chunks.append(rframe.to_ndarray())
    container.close()

    data = np.concatenate(chunks, axis=1) if chunks else np.zeros((1, 0), dtype=np.int16)
    samples = data.reshape(-1).astype("<i2")

    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TARGET_RATE)
        w.writeframes(samples.tobytes())
    return dst


def _ensure_wav_ffmpeg(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(TARGET_RATE), "-vn", "-f", "wav", str(dst)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {proc.stderr[-500:]}")
    return dst


def ensure_wav(src: Path, dst: Path) -> Path:
    """Convert `src` (any audio/video) to 16 kHz mono WAV at `dst`."""
    try:
        return _ensure_wav_pyav(src, dst)
    except Exception as exc:
        logger.warning("PyAV conversion failed (%s); trying system ffmpeg", exc)
        return _ensure_wav_ffmpeg(src, dst)


def get_duration(path: Path) -> float:
    """Return audio duration in seconds (wave stdlib → soundfile → PyAV)."""
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        pass
    try:
        import soundfile as sf

        info = sf.info(str(path))
        return float(info.frames) / float(info.samplerate)
    except Exception:
        pass
    try:
        import av

        container = av.open(str(path))
        dur = container.duration / 1_000_000 if container.duration else 0.0
        container.close()
        return float(dur)
    except Exception:
        return 0.0
