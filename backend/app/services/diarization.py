"""Speaker diarisation with pyannote.audio, plus merging diarisation turns onto
Whisper transcript segments.

If no HuggingFace token is configured, diarisation is skipped and every segment is
attributed to a single ``Speaker 1`` — the rest of the pipeline still works.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from ..config import get_settings

logger = logging.getLogger(__name__)

_pipeline = None


def diarization_available() -> bool:
    return bool(get_settings().hf_token)


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from pyannote.audio import Pipeline

        s = get_settings()
        # Export the token so EVERY internal huggingface_hub download (the pipeline pulls
        # several gated sub-models, e.g. speaker-diarization-community-1) authenticates,
        # not just the top-level from_pretrained call.
        if s.hf_token:
            os.environ["HF_TOKEN"] = s.hf_token
            os.environ["HUGGING_FACE_HUB_TOKEN"] = s.hf_token
        logger.info("Loading pyannote speaker-diarization-3.1 pipeline")
        try:
            # pyannote.audio >= 4 uses `token=`
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", token=s.hf_token
            )
        except TypeError:
            # pyannote.audio < 4 uses `use_auth_token=`
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", use_auth_token=s.hf_token
            )
        # Keep on CPU by default; pyannote on Apple MPS can be flaky.
        try:
            import torch

            if s.whisper_device == "cuda" and torch.cuda.is_available():
                _pipeline.to(torch.device("cuda"))
        except Exception:  # pragma: no cover
            pass
    return _pipeline


def diarize(wav_path: Path) -> list[dict[str, Any]]:
    """Return diarisation turns ``[{start, end, speaker}]`` (raw pyannote labels).

    Returns ``[]`` when diarisation is unavailable (no token / load failure), letting the
    caller fall back to a single speaker.
    """
    if not diarization_available():
        logger.warning("HF_TOKEN not set — skipping diarisation (single speaker).")
        return []
    try:
        pipeline = _get_pipeline()
        # Feed pyannote a pre-loaded waveform (via soundfile) instead of a path, so it does
        # NOT route audio decoding through torchcodec/torchaudio (which need the system
        # ffmpeg libs that are broken on this machine).
        import soundfile as sf
        import torch

        data, sr = sf.read(str(wav_path), dtype="float32", always_2d=True)  # (samples, channels)
        waveform = torch.from_numpy(data.T).contiguous()  # (channels, samples)
        result = pipeline({"waveform": waveform, "sample_rate": sr})
        # pyannote >= 4 returns a DiarizeOutput wrapping the Annotation; 3.x returns the
        # Annotation directly. Both expose `.itertracks(yield_label=True)`.
        annotation = getattr(result, "speaker_diarization", result)
        turns = [
            {"start": float(turn.start), "end": float(turn.end), "speaker": str(speaker)}
            for turn, _, speaker in annotation.itertracks(yield_label=True)
        ]
        return turns
    except Exception as exc:  # pragma: no cover
        logger.exception("Diarisation failed, falling back to single speaker: %s", exc)
        return []


# ---------------- merge ----------------
def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def _best_raw_speaker(start: float, end: float, turns: list[dict]) -> Optional[str]:
    best, best_ov = None, 0.0
    for t in turns:
        ov = _overlap(start, end, t["start"], t["end"])
        if ov > best_ov:
            best_ov, best = ov, t["speaker"]
    if best is None and turns:  # no overlap: pick nearest turn by midpoint
        mid = (start + end) / 2
        best = min(turns, key=lambda t: abs((t["start"] + t["end"]) / 2 - mid))["speaker"]
    return best


def assign_speakers(
    segments: list[dict], turns: list[dict]
) -> tuple[list[dict], list[str]]:
    """Attach a friendly ``speaker`` label (``Speaker 1..N``) to each transcript segment.

    Raw pyannote labels are remapped to ``Speaker N`` in order of first appearance, so the
    default labels are presentable and stable. Returns ``(segments, ordered_labels)``.
    """
    if not turns:
        for seg in segments:
            seg["speaker"] = "Speaker 1"
        return segments, (["Speaker 1"] if segments else [])

    order: list[str] = []
    for t in sorted(turns, key=lambda x: x["start"]):
        if t["speaker"] not in order:
            order.append(t["speaker"])
    mapping = {raw: f"Speaker {i + 1}" for i, raw in enumerate(order)}

    for seg in segments:
        raw = _best_raw_speaker(seg["start"], seg["end"], turns)
        seg["speaker"] = mapping.get(raw, "Speaker 1")

    labels = [mapping[r] for r in order]
    return segments, labels
