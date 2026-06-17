"""Offline smoke test for the voice pipeline (no API keys required).

Runs Whisper transcription + diarisation (single-speaker fallback without HF_TOKEN) on the
sample meeting and prints the transcript, plus a loose keyword-recall check.

Usage:  backend/venv/bin/python backend/scripts/selftest.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services import diarization, transcription  # noqa: E402

WAV = BACKEND.parent / "samples" / "standup.wav"


def main() -> None:
    print(f"Transcribing {WAV.name} ...")
    tr = transcription.transcribe(WAV)
    segs = tr["segments"]
    print(f"language={tr['language']}  duration={tr['duration']:.1f}s  segments={len(segs)}")

    turns = diarization.diarize(WAV)
    print(f"diarisation turns={len(turns)} (0 => no HF_TOKEN, single-speaker fallback)")
    segs, labels = diarization.assign_speakers(segs, turns)
    print(f"speakers={labels}")

    print("\n--- TRANSCRIPT ---")
    for s in segs:
        print(f'[{s["start"]:5.1f}-{s["end"]:5.1f}] {s["speaker"]}: {s["text"]}')

    full = " ".join(s["text"] for s in segs).lower()
    expected = [
        "pricing", "tuesday", "backend", "thursday", "pull request",
        "mockups", "annual billing", "performance", "friday",
    ]
    hits = [k for k in expected if k in full]
    print(f"\nKeyword recall: {len(hits)}/{len(expected)} -> {hits}")


if __name__ == "__main__":
    main()
