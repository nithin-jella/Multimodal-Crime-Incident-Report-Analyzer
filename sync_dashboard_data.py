"""Sync outputs/*.csv → dashboard/src/data/*.js for the React dashboard.

CSV column Incident_ID may use module prefixes: IMG-, AUD-, VID-, TXT-, DOC- (or legacy INC-).
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
IMAGE_CSV = PROJECT_ROOT / "outputs" / "image_output.csv"
AUDIO_CSV = PROJECT_ROOT / "outputs" / "audio_output.csv"
VIDEO_CSV = PROJECT_ROOT / "outputs" / "video_output.csv"
TEXT_CSV = PROJECT_ROOT / "outputs" / "text_output.csv"
DOCUMENT_CSV = PROJECT_ROOT / "outputs" / "document_output.csv"
IMAGE_JS = PROJECT_ROOT / "dashboard" / "src" / "data" / "imageResults.js"
AUDIO_JS = PROJECT_ROOT / "dashboard" / "src" / "data" / "audioResults.js"
VIDEO_JS = PROJECT_ROOT / "dashboard" / "src" / "data" / "videoResults.js"
TEXT_JS = PROJECT_ROOT / "dashboard" / "src" / "data" / "textResults.js"
DOCUMENT_JS = PROJECT_ROOT / "dashboard" / "src" / "data" / "docResults.js"


def sync_image() -> bool:
    if not IMAGE_CSV.exists():
        print(f"❌ Image CSV not found at {IMAGE_CSV}. Run: python modules/image_analyst.py")
        return False

    df = pd.read_csv(IMAGE_CSV)
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "incident_id": row["Incident_ID"],
                "image_id": row["Image_ID"],
                "scene_type": row["Scene_Type"],
                "objects_detected": row["Objects_Detected"],
                "text_extracted": row["Text_Extracted"],
                "confidence_score": round(float(row["Confidence_Score"]), 2),
            }
        )

    js_content = "export const imageResults = " + json.dumps(records, indent=2) + ";\n"
    IMAGE_JS.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_JS.write_text(js_content, encoding="utf-8")
    print(f"✅ Synced {len(records)} image rows → {IMAGE_JS.relative_to(PROJECT_ROOT)}")
    return True


def sync_audio() -> bool:
    if not AUDIO_CSV.exists():
        print(f"❌ Audio CSV not found at {AUDIO_CSV}. Run: python modules/audio_analyst.py")
        return False

    df = pd.read_csv(AUDIO_CSV)
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "incident_id": row["Incident_ID"],
                "call_id": row["Call_ID"],
                "transcript": row["Transcript"],
                "extracted_event": row["Extracted_Event"],
                "location": row["Location"],
                "sentiment": row["Sentiment"],
                "urgency_score": round(float(row["Urgency_Score"]), 2),
            }
        )

    js_content = "export const audioResults = " + json.dumps(records, indent=2) + ";\n"
    AUDIO_JS.parent.mkdir(parents=True, exist_ok=True)
    AUDIO_JS.write_text(js_content, encoding="utf-8")
    print(f"✅ Synced {len(records)} audio rows → {AUDIO_JS.relative_to(PROJECT_ROOT)}")
    return True


def sync_video() -> bool:
    if not VIDEO_CSV.exists():
        print(f"❌ Video CSV not found at {VIDEO_CSV}. Run: python modules/video_analyst.py")
        return False

    df = pd.read_csv(VIDEO_CSV)
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "incident_id": row["Incident_ID"],
                "timestamp": round(float(row["Timestamp"]), 2),
                "frame_id": row["Frame_ID"],
                "event_detected": row["Event_Detected"],
                "objects": row["Objects"],
                "confidence": round(float(row["Confidence"]), 2),
            }
        )

    js_content = "export const videoResults = " + json.dumps(records, indent=2) + ";\n"
    VIDEO_JS.parent.mkdir(parents=True, exist_ok=True)
    VIDEO_JS.write_text(js_content, encoding="utf-8")
    print(f"✅ Synced {len(records)} video rows → {VIDEO_JS.relative_to(PROJECT_ROOT)}")
    return True


def sync_text() -> bool:
    if not TEXT_CSV.exists():
        print(f"❌ Text CSV not found at {TEXT_CSV}. Run: python modules/text_analyst.py")
        return False

    df = pd.read_csv(TEXT_CSV)
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "incident_id": row["Incident_ID"],
                "text_id": str(row["Text_ID"]),
                "source_dataset": row["Source"],
                "raw_text": row["Raw_Text"],
                "sentiment": row["Sentiment"],
                "sentiment_score": round(float(row["Sentiment_Score"]), 4),
                "entities": row["Entities"],
                "topic": row["Topic"],
            }
        )

    js_content = "export const textResults = " + json.dumps(records, indent=2) + ";\n"
    TEXT_JS.parent.mkdir(parents=True, exist_ok=True)
    TEXT_JS.write_text(js_content, encoding="utf-8")
    print(f"✅ Synced {len(records)} text rows → {TEXT_JS.relative_to(PROJECT_ROOT)}")
    return True


def sync_document() -> bool:
    records = []
    if not DOCUMENT_CSV.exists():
        print(
            f"⚠️ Document CSV not found at {DOCUMENT_CSV}. "
            "Run: python modules/document_analyst.py — using empty docResults."
        )
    else:
        df = pd.read_csv(DOCUMENT_CSV)
        for _, row in df.iterrows():
            rid = row.get("Report_ID", row.get("Incident_ID", ""))
            records.append(
                {
                    "incident_id": str(rid),
                    "report_id": str(rid),
                    "incident_type": str(row.get("Incident_Type", "")),
                    "date": str(row.get("Date", "")),
                    "location": str(row.get("Location", "")),
                    "officer": str(row.get("Officer", "")),
                    "summary": str(row.get("Summary", "")),
                    "suspect_description": str(row.get("Suspect_Description", "")),
                    "outcome": str(row.get("Outcome", "")),
                }
            )
        print(f"✅ Synced {len(records)} document rows → {DOCUMENT_JS.relative_to(PROJECT_ROOT)}")

    js_content = "export const docResults = " + json.dumps(records, indent=2) + ";\n"
    DOCUMENT_JS.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENT_JS.write_text(js_content, encoding="utf-8")
    return bool(records)


def sync() -> None:
    sync_image()
    sync_audio()
    sync_video()
    sync_text()
    sync_document()
    print("   Run: cd dashboard && npm run dev")


if __name__ == "__main__":
    sync()
