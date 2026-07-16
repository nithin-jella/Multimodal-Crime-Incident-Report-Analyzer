"""
Multimodal Crime/Incident Report Analyzer — video pipeline (Module 4).
Processes all CCTV clips in data/videos/ (motion + YOLO). One row per detected event.
Incident_ID: VID-001, VID-002, ... globally across all videos.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import cv2
import pandas as pd

_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent
_DATA_VIDEOS = _PROJECT_ROOT / "data" / "videos"
_OUTPUTS = _PROJECT_ROOT / "outputs"
_VIDEO_EXTENSIONS = {".mpg", ".mpeg", ".mp4", ".avi", ".mov"}

_NO_VIDEOS_MSG = """[Video Analyst] ❌ No video files found in data/videos/
Download videos from: homepages.inf.ed.ac.uk/rbf/CAVIARDATA1
Place .mpg clips at: data/videos/"""


def _ensure_directories() -> None:
    _DATA_VIDEOS.mkdir(parents=True, exist_ok=True)
    _OUTPUTS.mkdir(parents=True, exist_ok=True)


def _list_videos() -> list[Path]:
    if not _DATA_VIDEOS.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(_DATA_VIDEOS.iterdir()):
        if p.is_file() and p.suffix.lower() in _VIDEO_EXTENSIONS:
            out.append(p)
    return out


def classify_event(
    detected_classes: list[str], motion: bool, person_count: int, rapid_motion_change: bool
) -> str:
    classes = [c.lower() for c in detected_classes]
    if not motion:
        return "No Event"
    if person_count >= 3:
        return "Crowd Gathering"
    if "person" in classes and rapid_motion_change:
        return "Anomaly Detected"
    if "car" in classes or "truck" in classes:
        return "Vehicle Movement"
    if "person" in classes:
        return "Person Movement"
    return "No Event"


def _frame_has_motion(
    prev_gray: cv2.typing.MatLike | None, frame, blur_ksize: int = 5, threshold_value: int = 25
) -> tuple[bool, float, cv2.typing.MatLike]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    if prev_gray is None:
        return False, 0.0, gray
    diff = cv2.absdiff(prev_gray, gray)
    _, thresh = cv2.threshold(diff, threshold_value, 255, cv2.THRESH_BINARY)
    changed = cv2.countNonZero(thresh)
    total = thresh.shape[0] * thresh.shape[1]
    ratio = (changed / total) if total else 0.0
    return ratio >= 0.05, ratio, gray


def _run_yolo(model, frame) -> tuple[list[str], float, int]:
    results = model(frame, verbose=False)
    if not results:
        return [], 0.0, 0
    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None or boxes.cls is None or len(boxes.cls) == 0:
        return [], 0.0, 0

    classes: list[str] = []
    confs: list[float] = []
    person_count = 0
    names = result.names
    for cls_id_tensor, conf_tensor in zip(boxes.cls.tolist(), boxes.conf.tolist()):
        cls_id = int(cls_id_tensor)
        cls_name = str(names.get(cls_id, cls_id))
        classes.append(cls_name)
        confs.append(float(conf_tensor))
        if cls_name.lower() == "person":
            person_count += 1

    uniq_classes = list(dict.fromkeys(classes))
    avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.0
    return uniq_classes, avg_conf, person_count


def _process_video(
    video_path: Path,
    model,
    incident_counter: int,
    frame_interval: int = 10,
) -> tuple[list[dict[str, object]], int]:
    """Return one row per non–No Event detection; advance global VID counter."""
    rows: list[dict[str, object]] = []
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path.name}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0

    prev_gray = None
    prev_motion_ratio = 0.0
    frame_id = -1

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_id += 1
        if frame_id % max(1, frame_interval) != 0:
            continue

        motion, motion_ratio, gray = _frame_has_motion(prev_gray, frame)
        prev_gray = gray
        if not motion:
            prev_motion_ratio = motion_ratio
            continue

        classes, conf, person_count = _run_yolo(model, frame)
        rapid_motion_change = abs(motion_ratio - prev_motion_ratio) >= 0.03
        prev_motion_ratio = motion_ratio

        event = classify_event(
            classes, motion=True, person_count=person_count, rapid_motion_change=rapid_motion_change
        )
        if event == "No Event":
            continue

        timestamp = round(frame_id / fps, 2)
        rows.append(
            {
                "Incident_ID": f"VID-{incident_counter:03d}",
                "Timestamp": timestamp,
                "Frame_ID": f"{video_path.stem}_frame_{frame_id}",
                "Event_Detected": event,
                "Objects": ", ".join(classes) if classes else "none",
                "Confidence": conf,
            }
        )
        incident_counter += 1

    cap.release()
    return rows, incident_counter


def run_video_pipeline(frame_interval: int = 10) -> None:
    _ensure_directories()
    videos = _list_videos()
    if not videos:
        print(_NO_VIDEOS_MSG)
        raise SystemExit(1)

    try:
        from ultralytics import YOLO
    except Exception as e:
        raise RuntimeError(
            f"Ultralytics is required for video analyst. Install with: pip install ultralytics ({e})"
        ) from e

    model = YOLO("yolov8n.pt")
    all_rows: list[dict[str, object]] = []
    incident_counter = 1
    for video in videos:
        try:
            rows, incident_counter = _process_video(
                video_path=video,
                model=model,
                incident_counter=incident_counter,
                frame_interval=frame_interval,
            )
            all_rows.extend(rows)
        except Exception as e:
            warnings.warn(f"Skipping video {video.name}: {e}", stacklevel=2)

    n_videos = len(videos)
    n_events = len(all_rows)

    out_df = pd.DataFrame(all_rows)
    if not out_df.empty:
        out_df = out_df[
            ["Incident_ID", "Timestamp", "Frame_ID", "Event_Detected", "Objects", "Confidence"]
        ]
    out_csv = _OUTPUTS / "video_output.csv"
    out_df.to_csv(out_csv, index=False)
    print(out_df.to_string(index=False))
    print(f"[Video Analyst] Processed {n_videos} videos, extracted {n_events} events", flush=True)


if __name__ == "__main__":
    run_video_pipeline()
