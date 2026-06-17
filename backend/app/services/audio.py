"""Audio utilities: normalise any upload to 16 kHz mono WAV and measure duration.

Both Whisper and pyannote are fed the same normalised WAV so their timestamps line up.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def ensure_wav(src: Path, dst: Path) -> Path:
    """Convert `src` (any ffmpeg-readable audio/video) to 16 kHz mono WAV at `dst`."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-ac", "1",        # mono
        "-ar", "16000",    # 16 kHz
        "-vn",             # drop any video stream
        "-f", "wav",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {proc.stderr[-500:]}")
    return dst


def get_duration(path: Path) -> float:
    """Return audio duration in seconds (tries soundfile, falls back to ffprobe)."""
    try:
        import soundfile as sf

        info = sf.info(str(path))
        return float(info.frames) / float(info.samplerate)
    except Exception:
        pass
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, check=True,
        )
        return float(out.stdout.strip() or 0.0)
    except Exception:
        return 0.0
