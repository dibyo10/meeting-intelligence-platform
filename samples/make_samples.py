"""Generate synthetic multi-speaker meeting recordings for testing.

Uses macOS `say` (distinct voices per speaker) + the stdlib `wave` module to concatenate —
no ffmpeg required. Each meeting is written as <name>.wav (16 kHz mono) in this folder.

    python samples/make_samples.py
"""
import subprocess
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAY_FMT = ["--file-format=WAVE", "--data-format=LEI16@16000"]

# Distinct macOS voices (verified present): Samantha=US♀ Daniel=GB♂ Rishi=IN♂ Karen=AU♀ Fred=US♂
MEETINGS: dict[str, list[tuple[str, str]]] = {
    "standup": [
        ("Samantha", "Good morning everyone. Let's start the weekly product sync. First item is the pricing page redesign. I think we should ship it next Tuesday."),
        ("Daniel", "Sounds good to me. I will finish the backend changes by Thursday and send the pull request for review."),
        ("Rishi", "I will update the mockups and share them with the team by tomorrow afternoon. One open question, do we support annual billing in this release?"),
        ("Samantha", "Good question. Let's decide the annual billing offline. David, can you also look into the performance regression we saw last week?"),
        ("Daniel", "Yes, I will investigate the performance issue and report back to the team on Friday."),
    ],
    "sprint_planning": [
        ("Samantha", "Welcome to sprint planning. Our main goal this sprint is to cut API latency below two hundred milliseconds and ship the new authentication service."),
        ("Daniel", "I will own the authentication service. I will have the OAuth integration and the Postgres migration done by Wednesday and open a pull request for review."),
        ("Rishi", "I will set up the Kubernetes autoscaling and the Redis cache to bring latency down. I should finish load testing by Thursday."),
        ("Karen", "I will write the integration tests for the auth flow. One open question, are we deprecating the old session based login in this release?"),
        ("Samantha", "Good point. Let's keep both for now and decide on deprecation next sprint. David, can you also document the new API endpoints?"),
        ("Daniel", "Sure, I will update the API documentation and add code examples by Friday."),
    ],
    "design_review": [
        ("Karen", "Let's review the new dashboard design. I think the navigation should move to a left sidebar for clarity."),
        ("Daniel", "Agreed. I will refactor the layout and share a Figma link by tomorrow morning."),
        ("Rishi", "I will run a quick usability test with five users this week and present the findings on Monday."),
        ("Karen", "Great. Let's make the sidebar the default and revisit the color palette after the usability results."),
    ],
}


def synth(voice: str, text: str, out: Path) -> None:
    subprocess.run(["say", "-v", voice, text, "-o", str(out), *SAY_FMT], check=True)


def build(name: str, lines: list[tuple[str, str]]) -> None:
    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, (voice, text) in enumerate(lines):
            p = Path(td) / f"seg{i}.wav"
            synth(voice, text, p)
            parts.append(p)
        out = HERE / f"{name}.wav"
        with wave.open(str(parts[0]), "rb") as w0:
            params = w0.getparams()
        with wave.open(str(out), "wb") as w:
            w.setparams(params)
            for p in parts:
                with wave.open(str(p), "rb") as r:
                    w.writeframes(r.readframes(r.getnframes()))
        with wave.open(str(out), "rb") as chk:
            secs = chk.getnframes() / chk.getframerate()
        speakers = len({v for v, _ in lines})
        print(f"  {name}.wav  —  {secs:4.1f}s, {speakers} speakers, {len(lines)} turns")


if __name__ == "__main__":
    print("Generating sample meetings:")
    for name, lines in MEETINGS.items():
        build(name, lines)
    print("Done. Files written to", HERE)
