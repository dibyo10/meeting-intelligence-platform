# Test recordings

The `.wav` files here are gitignored (regenerate them anytime). The app also accepts
**video** files (mp4/mov/webm) and other audio (mp3/m4a) — audio is extracted via PyAV.

## Synthetic samples (no download, instant)

Generate them with macOS `say` (no ffmpeg needed):

```bash
python samples/make_samples.py
```

| File | Length | Speakers | Good for testing |
|------|--------|----------|------------------|
| `standup.wav` | ~35 s | 3 | transcription, 3-speaker diarisation, 4 action items, open question |
| `sprint_planning.wav` | ~45 s | 4 | **technical vocab** (API, OAuth, Postgres, Kubernetes, Redis), 4 speakers, many action items + deadlines |
| `design_review.wav` | ~21 s | 3 | shorter meeting, decisions + next steps |

Edit the `MEETINGS` dict in `make_samples.py` to add your own scripted meetings (handy for
demoing specific features, e.g. lots of action items, or a noisy/edge case).

> Synthetic TTS voices are acoustically distinct and diarise well, but real human speech is
> the most convincing demo — see below.

## Real recordings (more authentic)

- **Record your own** — the strongest demo: 2–4 people talking for 1–3 minutes (a real
  standup, or just read the scripts in `make_samples.py` aloud with friends). Use the in-app
  **🎙️ Record live** button, or drop in a `.m4a`/`.mp4` from your phone.
- **Public-domain multi-speaker audio** (legal to use): US government press briefings,
  congressional/committee hearings (C-SPAN), or NASA press conferences — all public domain
  and genuinely multi-party.
- **Academic meeting datasets**: the **AMI Meeting Corpus**, **ICSI**, or **VoxConverse**
  (real recorded meetings with multiple speakers; ideal for stress-testing diarisation).
- **Podcasts / panel discussions** with 2–3 hosts work well for diarisation (for personal
  testing only — respect copyright).

## Tips for a good demo
- **Clear audio** keeps WER < 10% (the success metric); avoid heavy background noise for the headline demo, then optionally show a noisier clip to demonstrate robustness.
- **Keep it 1–3 minutes** so processing stays well under the 2-minute target on CPU.
- **≥ 3 distinct speakers** to show diarisation separating them.
- Bigger `WHISPER_MODEL` (`small`/`medium`) improves accuracy on harder audio at the cost of speed.
