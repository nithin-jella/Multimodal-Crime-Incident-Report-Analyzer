"""
Merge outputs from audio, image, video, text, and document pipelines into one CSV report.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd

_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent
_OUTPUTS = _PROJECT_ROOT / "outputs"

_AUDIO_CSV = _OUTPUTS / "audio_output.csv"
_IMAGE_CSV = _OUTPUTS / "image_output.csv"
_VIDEO_CSV = _OUTPUTS / "video_output.csv"
_TEXT_CSV = _OUTPUTS / "text_output.csv"
_DOCUMENT_CSV = _OUTPUTS / "document_output.csv"
_FINAL_CSV = _OUTPUTS / "final_integrated_report.csv"


def _location_from_entities(entities: str) -> str:
    if not entities or not isinstance(entities, str):
        return "N/A"
    m = re.search(r"Locations:\s*([^;]+)", entities)
    if not m:
        return "N/A"
    s = m.group(1).strip()
    return s if s and s != "N/A" else "N/A"


def _severity_level(score_10: float) -> str:
    if score_10 < 3:
        return "Low"
    if score_10 < 7:
        return "Medium"
    return "High"


def _clip(s: str, max_len: int = 500) -> str:
    s = str(s) if s is not None else ""
    s = " ".join(s.split())
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _load_audio_rows() -> list[dict[str, object]]:
    if not _AUDIO_CSV.is_file():
        return []
    df = pd.read_csv(_AUDIO_CSV)
    out: list[dict[str, object]] = []
    for _, row in df.iterrows():
        conf = float(row.get("Urgency_Score", 0) or 0)
        sev = round(min(10.0, max(0.0, conf * 10)), 2)
        out.append(
            {
                "Incident_ID": row["Incident_ID"],
                "Source": "Audio",
                "Type": row.get("Extracted_Event", ""),
                "Location": row.get("Location", "N/A") or "N/A",
                "Confidence/Urgency_Score": round(conf, 4),
                "Severity_Score": sev,
                "Severity_Level": _severity_level(sev),
                "Details": _clip(row.get("Transcript", "")),
            }
        )
    return out


def _load_image_rows() -> list[dict[str, object]]:
    if not _IMAGE_CSV.is_file():
        return []
    df = pd.read_csv(_IMAGE_CSV)
    out: list[dict[str, object]] = []
    for _, row in df.iterrows():
        conf = float(row.get("Confidence_Score", 0) or 0)
        sev = round(min(10.0, max(0.0, conf * 10)), 2)
        det = f"{row.get('Objects_Detected', '')} | OCR: {row.get('Text_Extracted', '')}"
        out.append(
            {
                "Incident_ID": row["Incident_ID"],
                "Source": "Image",
                "Type": row.get("Scene_Type", ""),
                "Location": "N/A",
                "Confidence/Urgency_Score": round(conf, 4),
                "Severity_Score": sev,
                "Severity_Level": _severity_level(sev),
                "Details": _clip(det),
            }
        )
    return out


def _load_video_rows() -> list[dict[str, object]]:
    if not _VIDEO_CSV.is_file():
        return []
    df = pd.read_csv(_VIDEO_CSV)
    out: list[dict[str, object]] = []
    for _, row in df.iterrows():
        conf = float(row.get("Confidence", 0) or 0)
        sev = round(min(10.0, max(0.0, conf * 10)), 2)
        det = f"{row.get('Frame_ID', '')} | {row.get('Objects', '')}"
        out.append(
            {
                "Incident_ID": row["Incident_ID"],
                "Source": "Video",
                "Type": row.get("Event_Detected", ""),
                "Location": "N/A",
                "Confidence/Urgency_Score": round(conf, 4),
                "Severity_Score": sev,
                "Severity_Level": _severity_level(sev),
                "Details": _clip(det),
            }
        )
    return out


def _load_text_rows() -> list[dict[str, object]]:
    if not _TEXT_CSV.is_file():
        return []
    df = pd.read_csv(_TEXT_CSV)
    out: list[dict[str, object]] = []
    for _, row in df.iterrows():
        conf = float(row.get("Sentiment_Score", 0) or 0)
        sev = round(min(10.0, max(0.0, conf * 10)), 2)
        loc = _location_from_entities(str(row.get("Entities", "")))
        raw = str(row.get("Raw_Text", row.get("Entities", "")))
        out.append(
            {
                "Incident_ID": row["Incident_ID"],
                "Source": "Text",
                "Type": row.get("Topic", ""),
                "Location": loc,
                "Confidence/Urgency_Score": round(conf, 4),
                "Severity_Score": sev,
                "Severity_Level": _severity_level(sev),
                "Details": _clip(raw),
            }
        )
    return out


def _document_urgency_score(incident_type: str) -> float:
    s = str(incident_type or "").lower()
    if any(k in s for k in ("homicide", "shooting", "weapon", "assault", "fire")):
        return 0.78
    if any(k in s for k in ("theft", "robbery", "disturbance", "traffic")):
        return 0.52
    if "administrative" in s or "training" in s or "other" in s:
        return 0.35
    return 0.45


def _load_document_rows() -> list[dict[str, object]]:
    if not _DOCUMENT_CSV.is_file():
        return []
    df = pd.read_csv(_DOCUMENT_CSV)
    out: list[dict[str, object]] = []
    for _, row in df.iterrows():
        inc_id = str(row.get("Report_ID") or row.get("Incident_ID") or "DOC-000")
        def _field(key: str) -> str:
            v = row.get(key)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return ""
            s = str(v).strip()
            return "" if s.lower() == "nan" else s

        itype = _field("Incident_Type") or "other / unspecified"
        conf = _document_urgency_score(itype)
        sev = round(min(10.0, max(0.0, conf * 10)), 2)
        loc = _field("Location") or "N/A"
        summ = _field("Summary")
        tail = " | ".join(
            x
            for x in (_field("Suspect_Description"), _field("Outcome"))
            if x and x != "N/A"
        )
        details = _clip(f"{summ} {tail}".strip())
        out.append(
            {
                "Incident_ID": inc_id,
                "Source": "Document",
                "Type": itype,
                "Location": loc,
                "Confidence/Urgency_Score": round(conf, 4),
                "Severity_Score": sev,
                "Severity_Level": _severity_level(sev),
                "Details": details,
            }
        )
    return out


def run_integration() -> None:
    """Merge all module CSVs into outputs/final_integrated_report.csv."""
    _OUTPUTS.mkdir(parents=True, exist_ok=True)

    audio_rows = _load_audio_rows()
    image_rows = _load_image_rows()
    video_rows = _load_video_rows()
    text_rows = _load_text_rows()
    document_rows = _load_document_rows()

    if not _AUDIO_CSV.is_file():
        warnings.warn(f"Missing {_AUDIO_CSV.name}; 0 audio rows in merge.", stacklevel=2)
    if not _IMAGE_CSV.is_file():
        warnings.warn(f"Missing {_IMAGE_CSV.name}; 0 image rows in merge.", stacklevel=2)
    if not _VIDEO_CSV.is_file():
        warnings.warn(f"Missing {_VIDEO_CSV.name}; 0 video rows in merge.", stacklevel=2)
    if not _TEXT_CSV.is_file():
        warnings.warn(f"Missing {_TEXT_CSV.name}; 0 text rows in merge.", stacklevel=2)
    if not _DOCUMENT_CSV.is_file():
        warnings.warn(f"Missing {_DOCUMENT_CSV.name}; 0 document rows in merge.", stacklevel=2)

    all_rows = audio_rows + image_rows + video_rows + text_rows + document_rows
    cols = [
        "Incident_ID",
        "Source",
        "Type",
        "Location",
        "Confidence/Urgency_Score",
        "Severity_Score",
        "Severity_Level",
        "Details",
    ]
    out_df = pd.DataFrame(all_rows, columns=cols) if all_rows else pd.DataFrame(columns=cols)

    out_df.to_csv(_FINAL_CSV, index=False)
    print(out_df.to_string(index=False))
    na, ni, nv, nt, nd = (
        len(audio_rows),
        len(image_rows),
        len(video_rows),
        len(text_rows),
        len(document_rows),
    )
    total = len(all_rows)
    print(
        f"Merged {na} audio + {ni} image + {nv} video + {nt} text + {nd} document incidents = {total} total",
        flush=True,
    )
    print(f"Wrote {_FINAL_CSV.relative_to(_PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    run_integration()
