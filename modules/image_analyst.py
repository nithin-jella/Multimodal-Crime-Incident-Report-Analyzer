"""
Multimodal Crime/Incident Report Analyzer — image pipeline.
Self-contained; no side effects on import.

Inference: Roboflow hosted fire model, with local yolov8n.pt fallback.
Images: fire-detection.v1i.yolov8/test/images/
"""

from __future__ import annotations

import os
import re
import sys
import warnings
from pathlib import Path

import cv2
import pandas as pd
import pytesseract

_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent
_OUTPUTS = _PROJECT_ROOT / "outputs"

try:
    from dotenv import load_dotenv

    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass  # pip install python-dotenv

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# --- Roboflow hosted model + local image folder (paths anchored to project root) ---
# Set ROBOFLOW_API_KEY in .env (see .env.example) or export in the shell
ROBOFLOW_API_KEY = (os.environ.get("ROBOFLOW_API_KEY") or "").strip()
ROBOFLOW_WORKSPACE = "leilamegdiche"
ROBOFLOW_PROJECT = "fire-detection-rsqrr"
ROBOFLOW_VERSION = 1
# Equivalent to Path("fire-detection.v1i.yolov8/test/images") when running from project root
IMAGE_DIR = _PROJECT_ROOT / "fire-detection.v1i.yolov8" / "test" / "images"

_TESSERACT_HINT = """[Image Analyst] ⚠️ Tesseract not found. Install it:
  Mac:    brew install tesseract
  Ubuntu: sudo apt install tesseract-ocr"""

_MISSING_FOLDER_MSG = (
    "[Image Analyst] ❌ Expected folder not found or empty:\n"
    f"  {IMAGE_DIR.relative_to(_PROJECT_ROOT)}\n"
    "Ensure fire-detection.v1i.yolov8 is present at the project root with test/images/."
)


def _ensure_directories() -> None:
    _OUTPUTS.mkdir(parents=True, exist_ok=True)


def _list_sorted_test_images() -> list[Path]:
    if not IMAGE_DIR.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(IMAGE_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS:
            out.append(p)
    return out


def classify_scene(detected_classes: str | list[str], filename: str = "") -> str:
    """
    Map detections to scene type (dataset: fire, smoke, light, no-fire).
    Must check 'no-fire' before 'fire' — substring 'fire' appears inside 'no-fire'.
    """
    _ = filename
    if isinstance(detected_classes, list):
        classes = ",".join(str(c) for c in detected_classes).lower()
    else:
        classes = str(detected_classes).strip().lower()
    if classes in ("none", "detection unavailable", ""):
        return "Unknown"
    if "no-fire" in classes:
        return "No Fire Detected"
    if "fire" in classes or "smoke" in classes or "light" in classes:
        return "Fire"
    if "car" in classes or "truck" in classes:
        return "Accident"
    if "person" in classes:
        return "Suspicious Activity"
    return "Unknown"


def _normalize_confidence(c: float) -> float:
    if c > 1.0:
        return min(1.0, c / 100.0)
    return float(c)


def _roboflow_result_to_detections(result: dict) -> tuple[str, float, bool]:
    predictions = result.get("predictions", [])
    if not predictions:
        return "none", 0.0, True
    names: list[str] = []
    confs: list[float] = []
    for p in predictions:
        cls_name = p.get("class") or p.get("class_name") or ""
        if cls_name:
            names.append(str(cls_name))
        c = p.get("confidence", 0.0)
        try:
            confs.append(_normalize_confidence(float(c)))
        except (TypeError, ValueError):
            confs.append(0.0)
    if not names:
        return "none", 0.0, True
    avg_conf = round(sum(confs) / len(confs), 2)
    return ",".join(names), avg_conf, True


def _run_roboflow_predict(rf_model: object, path: Path) -> tuple[str, float, bool]:
    # result = model.predict(...).json()  ->  {"predictions": [{class, confidence}, ...]}
    p = rf_model.predict(str(path), confidence=40, overlap=30)
    result = p.json() if hasattr(p, "json") else (p if isinstance(p, dict) else {})
    if not isinstance(result, dict):
        result = {}
    return _roboflow_result_to_detections(result)


def _run_yolo_on_image(
    model: object | None, path: Path
) -> tuple[str, float, bool]:
    if model is None:
        return "detection unavailable", 0.0, False
    try:
        results = model(str(path), verbose=False)
        names: list[str] = []
        confs: list[float] = []
        for r in results:
            boxes = getattr(r, "boxes", None)
            if boxes is None or len(boxes) == 0:
                continue
            rnames = getattr(r, "names", {})
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                label = rnames.get(cls_id, str(cls_id))
                names.append(str(label))
                confs.append(float(boxes.conf[i].item()))
        if not names:
            return "none", 0.0, True
        avg_conf = round(sum(confs) / len(confs), 2)
        return ",".join(names), avg_conf, True
    except Exception:
        return "detection unavailable", 0.0, False


def _detection_for_image(
    rf_model: object | None,
    fallback_yolo: object | None,
    path: Path,
) -> tuple[str, float, bool]:
    if rf_model is not None:
        try:
            return _run_roboflow_predict(rf_model, path)
        except Exception as e:
            warnings.warn(
                f"Roboflow inference failed for {path.name} ({e}); using yolov8n.pt fallback.",
                stacklevel=2,
            )
    if fallback_yolo is not None:
        return _run_yolo_on_image(fallback_yolo, path)
    return "detection unavailable", 0.0, False


def _ocr_image(path: Path) -> str:
    try:
        img = cv2.imread(str(path))
        if img is None:
            return "none"
        try:
            raw = pytesseract.image_to_string(img)
        except Exception:
            print(_TESSERACT_HINT, flush=True)
            return "OCR unavailable"
        text = " ".join(raw.split())
        text = re.sub(r"[^\x00-\x7F]+", "", text)
        text = text.strip()
        return text if text else "none"
    except Exception:
        print(_TESSERACT_HINT, flush=True)
        return "OCR unavailable"


def _process_one_image(
    path: Path,
    rf_model: object | None,
    fallback_yolo: object | None,
    index: int,
) -> dict[str, object]:
    row: dict[str, object] = {
        "Incident_ID": f"IMG-{index:03d}",
        "Image_ID": path.stem,
        "Scene_Type": "Unknown",
        "Objects_Detected": "none",
        "Text_Extracted": "none",
        "Confidence_Score": 0.0,
    }
    try:
        objs, conf, ok = _detection_for_image(rf_model, fallback_yolo, path)
        row["Objects_Detected"] = objs
        row["Confidence_Score"] = conf
        if not ok or objs == "detection unavailable":
            row["Objects_Detected"] = "detection unavailable"
            row["Confidence_Score"] = 0.0
            row["Scene_Type"] = classify_scene("detection unavailable")
        else:
            row["Scene_Type"] = classify_scene(objs)

        row["Text_Extracted"] = _ocr_image(path)
    except Exception as e:
        warnings.warn(f"Skipping {path}: {e}", stacklevel=2)
        row["Scene_Type"] = "Unknown"
        row["Objects_Detected"] = "detection unavailable"
        row["Confidence_Score"] = 0.0
    return row


def run_image_pipeline() -> None:
    _ensure_directories()

    print(
        "[Image Analyst] Loading real fire detection images from "
        "fire-detection.v1i.yolov8/test/images/",
        flush=True,
    )

    all_sorted = _list_sorted_test_images()
    total = len(all_sorted)
    if total == 0:
        print(_MISSING_FOLDER_MSG)
        sys.exit(1)

    print(
        f"[Image Analyst] Found {total} images. Processing all...",
        flush=True,
    )

    image_paths = all_sorted

    rf_model = None
    try:
        from roboflow import Roboflow

        if not ROBOFLOW_API_KEY:
            warnings.warn(
                "ROBOFLOW_API_KEY not set; using yolov8n.pt only. "
                "Add it to .env or export ROBOFLOW_API_KEY (see .env.example).",
                stacklevel=2,
            )
        else:
            rf = Roboflow(api_key=ROBOFLOW_API_KEY)
            project = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT)
            rf_model = project.version(ROBOFLOW_VERSION).model
    except Exception as e:
        warnings.warn(f"Roboflow model unavailable ({e}); will use yolov8n.pt fallback.", stacklevel=2)

    fallback_yolo = None
    try:
        from ultralytics import YOLO

        fallback_yolo = YOLO("yolov8n.pt")
    except Exception as e:
        warnings.warn(f"yolov8n.pt unavailable ({e}).", stacklevel=2)

    if rf_model is None and fallback_yolo is None:
        warnings.warn("No inference backend available.", stacklevel=2)

    rows: list[dict[str, object]] = []
    for i, path in enumerate(image_paths, start=1):
        try:
            rows.append(_process_one_image(path, rf_model, fallback_yolo, i))
        except Exception as e:
            warnings.warn(f"Skipping {path}: {e}", stacklevel=2)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[
            [
                "Incident_ID",
                "Image_ID",
                "Scene_Type",
                "Objects_Detected",
                "Text_Extracted",
                "Confidence_Score",
            ]
        ]

    out_csv = _OUTPUTS / "image_output.csv"
    df.to_csv(out_csv, index=False)
    print(df.to_string(index=False))
    print(f"[Image Analyst] Processed {len(image_paths)} fire detection images", flush=True)


if __name__ == "__main__":
    run_image_pipeline()
