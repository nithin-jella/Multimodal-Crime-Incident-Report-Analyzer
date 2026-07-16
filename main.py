#!/usr/bin/env python3
"""
Run all multimodal pipelines end-to-end (audio, image, video, text, documents), then merge outputs.
Each step is isolated: failures are logged and the script continues.
"""

from __future__ import annotations

import traceback


def _run_step(name: str, fn) -> None:
    print(f"\n{name}", flush=True)
    try:
        fn()
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"   ⚠️ Exited with code {e.code}", flush=True)
    except Exception as e:
        print(f"   ⚠️ Error: {e}", flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60, flush=True)
    print("🚨 Multimodal Crime/Incident Report Analyzer", flush=True)
    print("=" * 60, flush=True)

    from modules.audio_analyst import run_audio_pipeline

    _run_step("[1/6] Running Audio Analyst...", run_audio_pipeline)

    from modules.image_analyst import run_image_pipeline

    _run_step("[2/6] Running Image Analyst...", run_image_pipeline)

    from modules.video_analyst import run_video_pipeline

    _run_step("[3/6] Running Video Analyst...", run_video_pipeline)

    from modules.text_analyst import run_text_pipeline

    _run_step("[4/6] Running Text Analyst...", run_text_pipeline)

    from modules.document_analyst import run_document_pipeline

    _run_step("[5/6] Running Document Analyst...", run_document_pipeline)

    from modules.integrator import run_integration

    _run_step("[6/6] Running Integration...", run_integration)

    print("\n" + "=" * 60, flush=True)
    print("✅ Pipeline complete!", flush=True)
    print("📊 Open dashboard: cd dashboard && npm run dev", flush=True)
    print("=" * 60, flush=True)
