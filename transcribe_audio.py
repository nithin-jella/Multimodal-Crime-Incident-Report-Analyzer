"""
Transcribe all .mp3 / .wav files in data/audio/ with OpenAI Whisper (base model).
Writes data/audio/transcripts.csv with columns: call_id, transcript.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_AUDIO = PROJECT_ROOT / "data" / "audio"
TRANSCRIPTS_CSV = DATA_AUDIO / "transcripts.csv"

_AUDIO_EXTENSIONS = {".mp3", ".wav"}


def _list_audio_files() -> list[Path]:
    if not DATA_AUDIO.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(DATA_AUDIO.iterdir()):
        if p.is_file() and p.suffix.lower() in _AUDIO_EXTENSIONS:
            out.append(p)
    return out


def main() -> None:
    DATA_AUDIO.mkdir(parents=True, exist_ok=True)

    import whisper

    model = whisper.load_model("base")

    files = _list_audio_files()
    if not files:
        print(f"No .mp3 or .wav files found in {DATA_AUDIO.relative_to(PROJECT_ROOT)}/")
        return

    rows: list[dict[str, str]] = []
    for audio_path in files:
        call_id = audio_path.stem
        print(f"Transcribing {audio_path.name}...", flush=True)
        try:
            result = model.transcribe(str(audio_path))
            text = (result.get("text") or "").strip()
            rows.append({"call_id": call_id, "transcript": text})
        except Exception as e:
            warnings.warn(f"Skipping {audio_path.name}: {e}", stacklevel=2)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[["call_id", "transcript"]]

    df.to_csv(TRANSCRIPTS_CSV, index=False)
    print(df.to_string(index=False))
    print(f"\n✅ Saved {TRANSCRIPTS_CSV.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
