"""
As the fifth module of the Multimodal Crime/Incident Report Analyzer, the text pipeline is responsible for parsing unstructured text. It automatically reads incident data originating from social media and news outlets, utilizing either the crimereport.csv or crimereport.txt files found in the data/text/ directory (based on the Kaggle CrimeReport dataset).
"""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent
_DATA_TEXT = _PROJECT_ROOT / "data" / "text"
# Kaggle ships JSON-lines tweets as CrimeReport.txt (case-sensitive on macOS/Linux).
_DATASET_CANDIDATES = (
    _DATA_TEXT / "crimereport.csv",
    _DATA_TEXT / "crimereport.txt",
    _DATA_TEXT / "CrimeReport.csv",
    _DATA_TEXT / "CrimeReport.txt",
)
_OUTPUTS = _PROJECT_ROOT / "outputs"
_SOURCE_LABEL = "Kaggle CrimeReport"

_NO_DATASET_MSG = """[Text Analyst] ❌ No text dataset found under data/text/
Expected one of: crimereport.csv, crimereport.txt, CrimeReport.csv, CrimeReport.txt
(JSON-lines Twitter export or a CSV with a text column)
Download from: kaggle.com/datasets/cameliasiadat/crimereport"""

_TOPIC_LABELS = [
    "accident",
    "fire",
    "theft",
    "public disturbance",
    "assault",
    "other",
]

_KEYWORD_TOPIC = (
    (("accident", "crash", "collision", "vehicle"), "accident"),
    (("fire", "burning", "flame", "smoke"), "fire"),
    (("theft", "stolen", "robbery", "burglary"), "theft"),
    (("disturbance", "fight", "riot", "crowd"), "public disturbance"),
    (("assault", "attack", "shooting", "stab", "weapon"), "assault"),
)


def _ensure_directories() -> None:
    _DATA_TEXT.mkdir(parents=True, exist_ok=True)
    _OUTPUTS.mkdir(parents=True, exist_ok=True)


def _resolve_dataset_path() -> Path | None:
    for p in _DATASET_CANDIDATES:
        if p.is_file():
            return p
    return None


def _read_crime_dataset(path: Path) -> pd.DataFrame:
    """Load Kaggle CrimeReport: JSON-lines (one tweet JSON per line) or CSV/TSV."""
    # Primary format from the dataset: newline-delimited JSON (Twitter objects with a "text" field).
    try:
        df = pd.read_json(path, lines=True)
        if len(df.columns) > 0:
            return df
    except Exception:
        pass

    last_err: Exception | None = None
    for sep in (",", "\t"):
        try:
            return pd.read_csv(path, sep=sep)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Could not parse {path} as JSONL or CSV/TSV: {last_err}") from last_err


def _find_text_column(df: pd.DataFrame) -> str:
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for key in (
        "text",
        "full_text",
        "description",
        "content",
        "report",
        "tweet",
        "body",
        "message",
        "article",
        "story",
        "title",
    ):
        if key in cols_lower:
            return cols_lower[key]

    # Heuristic: use the string column with the longest average length (unstructured exports).
    best_col = None
    best_avg = 0.0
    for col in df.columns:
        ser = df[col]
        if ser.dtype != object and not str(ser.dtype).startswith("string"):
            continue
        try:
            avg = float(ser.astype(str).str.len().mean())
        except Exception:
            continue
        if avg > best_avg and avg > 20:
            best_avg = avg
            best_col = col
    if best_col is not None:
        warnings.warn(
            f"No standard text column name; using longest text-like column {best_col!r}.",
            stacklevel=2,
        )
        return best_col

    raise ValueError(
        "Could not auto-detect text column (expected text, full_text, description, content, report, …)."
    )


def _clean_text(raw: str) -> str:
    s = raw.lower()
    s = re.sub(r"https?://\S+|www\.\S+", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _ensure_nltk_resources() -> None:
    import nltk

    for pkg in ("stopwords", "punkt", "punkt_tab"):
        nltk.download(pkg, quiet=True)


def _nltk_tokenize_remove_stopwords(text: str) -> str:
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize

        _ensure_nltk_resources()
        stop_words = set(stopwords.words("english"))
        tokens = word_tokenize(text)
        out = [w for w in tokens if w.isalnum() and w not in stop_words]
        return " ".join(out)
    except Exception as e:
        warnings.warn(f"NLTK preprocess failed ({e}); using cleaned text only.", stacklevel=2)
        return text


def _entities_string(doc) -> str:
    people: list[str] = []
    locs: list[str] = []
    orgs: list[str] = []
    dates: list[str] = []
    for ent in doc.ents:
        t = ent.text.strip()
        if not t:
            continue
        if ent.label_ == "PERSON":
            people.append(t)
        elif ent.label_ in ("GPE", "LOC"):
            locs.append(t)
        elif ent.label_ == "ORG":
            orgs.append(t)
        elif ent.label_ == "DATE":
            dates.append(t)

    def join_unique(xs: list[str]) -> str:
        return "; ".join(dict.fromkeys(xs))

    p = join_unique(people)
    l_ = join_unique(locs)
    o = join_unique(orgs)
    d = join_unique(dates)
    return (
        f"People: {p or 'N/A'}; Locations: {l_ or 'N/A'}; Organizations: {o or 'N/A'}; Dates: {d or 'N/A'}"
    )


def _keyword_topic(clean_lower: str) -> str:
    for keywords, label in _KEYWORD_TOPIC:
        if any(k in clean_lower for k in keywords):
            return label
    return "other"


def _sentiment_pipeline():
    from transformers import pipeline

    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
    )


def _zero_shot_pipeline():
    from transformers import pipeline

    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
    )


def analyze_single_text(
    raw: str,
    idx: int,
    *,
    id_prefix: str = "TXT",
    text_id: str | int | None = None,
    source_label: str | None = None,
    nlp: Any = None,
    sentiment_pipe: Any = None,
    zs_pipe: Any = None,
) -> dict[str, object] | None:
    """
    Run the same NLP stack as the text pipeline on one string.
    Used by the text dataset iterator and by document_analyst (PDF/DOCX).
    """
    raw_for_preview = raw.strip()
    if not raw_for_preview:
        return None

    if source_label is None:
        source_label = _SOURCE_LABEL
    if text_id is None:
        text_id = idx

    try:
        raw_100 = raw_for_preview[:100] if raw_for_preview else ""

        cleaned = _clean_text(raw)
        _nltk_tokenize_remove_stopwords(cleaned)

        if nlp is not None:
            doc = nlp(raw_for_preview or cleaned)
            entities = _entities_string(doc)
        else:
            entities = "People: N/A; Locations: N/A; Organizations: N/A; Dates: N/A"

        snippet = (raw_for_preview or cleaned)[:512]

        sentiment_label = "NEGATIVE"
        sentiment_score = 0.5
        if sentiment_pipe is not None:
            out = sentiment_pipe(snippet)
            if out:
                label = str(out[0].get("label", "")).upper()
                sentiment_score = float(out[0].get("score", 0.5))
                if "POS" in label or label == "LABEL_1":
                    sentiment_label = "POSITIVE"
                else:
                    sentiment_label = "NEGATIVE"

        topic = "other"
        if zs_pipe is not None and snippet.strip():
            try:
                z = zs_pipe(snippet, candidate_labels=_TOPIC_LABELS, multi_label=False)
                labels = z.get("labels") or []
                if labels:
                    topic = str(labels[0]).lower()
            except Exception as e:
                warnings.warn(f"Zero-shot failed for row {idx}: {e}", stacklevel=2)
                topic = _keyword_topic(cleaned)
        else:
            topic = _keyword_topic(cleaned)

        return {
            "Incident_ID": f"{id_prefix}-{idx:03d}",
            "Text_ID": str(text_id) if text_id is not None else str(idx),
            "Source": source_label,
            "Raw_Text": raw_100,
            "Sentiment": sentiment_label,
            "Sentiment_Score": round(sentiment_score, 4),
            "Entities": entities,
            "Topic": topic,
        }
    except Exception as e:
        warnings.warn(f"Skipping row {idx}: {e}", stacklevel=2)
        return None


def run_text_pipeline() -> None:
    _ensure_directories()
    dataset_path = _resolve_dataset_path()
    if dataset_path is None:
        print(_NO_DATASET_MSG)
        sys.exit(1)

    try:
        df = _read_crime_dataset(dataset_path)
    except Exception as e:
        raise RuntimeError(f"Could not read {dataset_path}: {e}") from e

    text_col = _find_text_column(df)

    nlp = None
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        warnings.warn(f"spaCy unavailable ({e}); entity extraction will be empty.", stacklevel=2)

    sentiment_pipe = None
    try:
        sentiment_pipe = _sentiment_pipeline()
    except Exception as e:
        warnings.warn(f"HuggingFace sentiment unavailable ({e}).", stacklevel=2)

    zs_pipe = None
    try:
        zs_pipe = _zero_shot_pipeline()
    except Exception as e:
        warnings.warn(f"Zero-shot classifier unavailable ({e}); using keyword topic fallback.", stacklevel=2)

    rows: list[dict[str, object]] = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        raw = str(row.get(text_col, "") or "")
        text_id = row.get("id", row.get("ID", idx))
        out = analyze_single_text(
            raw,
            idx,
            text_id=text_id,
            nlp=nlp,
            sentiment_pipe=sentiment_pipe,
            zs_pipe=zs_pipe,
        )
        if out:
            rows.append(out)

    out_df = pd.DataFrame(rows)
    if not out_df.empty:
        out_df = out_df[
            [
                "Incident_ID",
                "Text_ID",
                "Source",
                "Raw_Text",
                "Sentiment",
                "Sentiment_Score",
                "Entities",
                "Topic",
            ]
        ]

    out_csv = _OUTPUTS / "text_output.csv"
    out_df.to_csv(out_csv, index=False)
    print(out_df.to_string(index=False))
    print(f"[Text Analyst] Processed {len(df)} crime reports", flush=True)


if __name__ == "__main__":
    run_text_pipeline()
