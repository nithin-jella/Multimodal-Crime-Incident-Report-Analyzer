"""
Multimodal Crime/Incident Report Analyzer — audio pipeline (Module 1).
Self-contained; no side effects on import.

Reads data/audio/transcripts.csv (e.g. from transcribe_audio.py or Kaggle export).
"""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

import pandas as pd

_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent

try:
    from dotenv import load_dotenv

    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

_DATA_AUDIO = _PROJECT_ROOT / "data" / "audio"
_TRANSCRIPTS_CSV = _DATA_AUDIO / "transcripts.csv"
_OUTPUTS = _PROJECT_ROOT / "outputs"

_NO_TRANSCRIPTS_MSG = """[Audio Analyst] ❌ No transcripts file found at data/audio/transcripts.csv
Steps to fix:
  • Run: python transcribe_audio.py   (Whisper — needs .mp3/.wav in data/audio/)
  • Or download CSV from kaggle.com/code/stpeteishii/911-calls-wav2vec2 and save as data/audio/transcripts.csv"""

_URGENCY_WORDS = (
    "help",
    "hurry",
    "trapped",
    "emergency",
    "urgent",
    "violent",
    "injured",
    "dead",
    "dying",
)

_STREET_REGEX = re.compile(
    r"\b\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?\s+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Drive|Dr\.?)\b",
    re.IGNORECASE,
)
_HIGHWAY_REGEX = re.compile(r"\bHighway\s+\d+\b", re.IGNORECASE)
_EXIT_REGEX = re.compile(r"\bExit\s+\d+\b", re.IGNORECASE)


def _ensure_directories() -> None:
    _DATA_AUDIO.mkdir(parents=True, exist_ok=True)
    _OUTPUTS.mkdir(parents=True, exist_ok=True)


def _normalize_transcript_columns(df: pd.DataFrame) -> pd.DataFrame:
    colmap = {c.lower().strip(): c for c in df.columns}
    cid = None
    txt = None
    for key in ("call_id", "call id", "callid", "id"):
        if key in colmap:
            cid = colmap[key]
            break
    for key in ("transcript", "text", "transcription"):
        if key in colmap:
            txt = colmap[key]
            break
    if cid is None or txt is None:
        raise ValueError("CSV must contain call_id and transcript columns (case-insensitive).")
    out = df[[cid, txt]].copy()
    out.columns = ["call_id", "transcript"]
    return out


def _regex_locations(text: str) -> list[str]:
    found: list[str] = []
    for rx in (_STREET_REGEX, _HIGHWAY_REGEX, _EXIT_REGEX):
        for m in rx.finditer(text):
            s = m.group(0).strip()
            if s and s not in found:
                found.append(s)
    return found


def _extract_location(transcript: str, nlp) -> str:
    if not transcript.strip():
        return "Unknown"
    if nlp is not None:
        try:
            doc = nlp(transcript)
            ents = [e.text.strip() for e in doc.ents if e.label_ in ("GPE", "LOC")]
            ents = [e for e in ents if e]
            if ents:
                return ", ".join(dict.fromkeys(ents))
        except Exception as e:
            warnings.warn(f"spaCy NER failed: {e}", stacklevel=2)
    locs = _regex_locations(transcript)
    if locs:
        return ", ".join(dict.fromkeys(locs))
    return "Unknown"


def _word_in_text(t_lower: str, phrase: str) -> bool:
    """Match phrase with word boundaries (avoids 'car' in 'scare')."""
    if " " in phrase.strip():
        return phrase.lower() in t_lower
    return re.search(rf"\b{re.escape(phrase.lower())}\b", t_lower) is not None


def _any_keyword(t_lower: str, keywords: tuple[str, ...]) -> bool:
    return any(_word_in_text(t_lower, k) for k in keywords)


def _classify_event(transcript: str) -> str:
    t = transcript.lower()
    if _any_keyword(t, ("fire", "burning", "flames", "smoke")):
        return "Fire"
    if _any_keyword(t, ("accident", "crash", "collision", "car", "vehicle")):
        return "Road Accident"
    if _any_keyword(t, ("stab", "shoot", "gun", "weapon", "assault", "knife")):
        return "Assault"
    if _any_keyword(t, ("broke", "theft", "stolen", "robbery", "burglary")):
        return "Theft"
    if _any_keyword(t, ("fight", "violent", "disturbance", "brawl")):
        return "Public Disturbance"
    if "suspicious" in t:
        return "Suspicious Activity"
    return "Unknown Incident"


def _urgency_word_boost(transcript: str) -> float:
    """+0.1 for each urgency word that appears at least once."""
    t = transcript.lower()
    boost = 0.0
    for w in _URGENCY_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", t):
            boost += 0.1
    return boost


def _sentiment_and_urgency(transcript: str, sentiment_pipeline):
    snippet = transcript[:512] if transcript else ""
    if sentiment_pipeline is not None:
        try:
            out = sentiment_pipeline(snippet)
            if not out:
                raise ValueError("empty sentiment output")
            label = str(out[0].get("label", "")).upper()
            score = float(out[0].get("score", 0.0))
            if "NEG" in label or label == "LABEL_0":
                sentiment = "NEGATIVE"
                base = score
            elif "POS" in label or label == "LABEL_1":
                sentiment = "POSITIVE"
                base = 1.0 - score
            else:
                sentiment = "NEGATIVE"
                base = 0.5
            boost = _urgency_word_boost(transcript)
            urgency = max(0.0, min(1.0, base + boost))
            urgency = round(urgency, 2)
            return sentiment, urgency
        except Exception as e:
            warnings.warn(f"Sentiment pipeline failed: {e}", stacklevel=2)

    count = sum(
        1
        for w in _URGENCY_WORDS
        if re.search(rf"\b{re.escape(w)}\b", transcript.lower())
    )
    urgency = round(min(count * 0.15, 1.0), 2)
    sentiment = "NEGATIVE" if count > 0 else "POSITIVE"
    return sentiment, urgency


def run_audio_pipeline() -> None:
    """Main entry point called by main.py"""
    _ensure_directories()

    if not _TRANSCRIPTS_CSV.is_file():
        print(_NO_TRANSCRIPTS_MSG)
        sys.exit(1)

    try:
        raw = pd.read_csv(_TRANSCRIPTS_CSV)
        df = _normalize_transcript_columns(raw)
    except Exception as e:
        raise RuntimeError(
            f"Could not read or parse transcripts CSV (need call_id and transcript columns): {e}"
        ) from e

    nlp = None
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm")
    except OSError as e:
        warnings.warn(f"spaCy model missing ({e}); using regex-only location extraction.", stacklevel=2)
    except Exception as e:
        warnings.warn(f"spaCy load failed ({e}); using regex-only location extraction.", stacklevel=2)

    sentiment_pipeline = None
    try:
        from transformers import pipeline

        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
    except Exception as e:
        warnings.warn(f"HuggingFace sentiment unavailable ({e}); using keyword urgency fallback.", stacklevel=2)

    rows: list[dict[str, object]] = []
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        call_id = str(getattr(row, "call_id", "") or "").strip()
        transcript = str(getattr(row, "transcript", "") or "")
        try:
            location = _extract_location(transcript, nlp)
            event = _classify_event(transcript)
            sentiment, urgency = _sentiment_and_urgency(transcript, sentiment_pipeline)
            rows.append(
                {
                    "Incident_ID": f"AUD-{idx:03d}",
                    "Call_ID": call_id if call_id else f"row_{idx}",
                    "Transcript": transcript,
                    "Extracted_Event": event,
                    "Location": location,
                    "Sentiment": sentiment,
                    "Urgency_Score": urgency,
                }
            )
        except Exception as e:
            warnings.warn(f"Skipping transcript row {idx}: {e}", stacklevel=2)

    out_df = pd.DataFrame(rows)
    if not out_df.empty:
        out_df = out_df[
            [
                "Incident_ID",
                "Call_ID",
                "Transcript",
                "Extracted_Event",
                "Location",
                "Sentiment",
                "Urgency_Score",
            ]
        ]

    out_csv = _OUTPUTS / "audio_output.csv"
    out_df.to_csv(out_csv, index=False)
    print(out_df.to_string(index=False))
    print(f"[Audio Analyst] Processed {len(df)} transcripts", flush=True)


if __name__ == "__main__":
    run_audio_pipeline()
