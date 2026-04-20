from __future__ import annotations

import shutil
from pathlib import Path
import sys

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task2_backend.main import create_app


def _write_test_config(tmp_path: Path, media_dir: Path) -> Path:
    config_path = tmp_path / "config.yaml"
    config = {
        "paths": {
            "input_dir": str(media_dir.resolve()),
            "normalized_dir": str((tmp_path / "workspace/normalized").resolve()),
            "export_dir": str((tmp_path / "exports").resolve()),
            "log_dir": str((tmp_path / "logs").resolve()),
            "database_path": str((tmp_path / "data/task2.db").resolve()),
            "temp_dir": str((tmp_path / "workspace/tmp").resolve()),
        },
        "runtime": {
            "mode": "test",
            "worker_enabled": False,
            "maintenance_interval_seconds": 30,
            "max_concurrent_jobs": 1,
            "shutdown_grace_seconds": 5,
        },
        "annotation": {
            "autosave_interval_seconds": 15,
            "heartbeat_interval_seconds": 15,
            "task_lock_timeout_seconds": 300,
            "allowed_primary_labels": ["neutral", "happy", "sad", "angry", "fear", "surprise", "disgust", "other"],
            "enable_secondary_labels": True,
            "enable_valence_arousal": True,
        },
        "media": {
            "supported_audio_extensions": [".wav", ".mp3", ".flac", ".m4a"],
            "supported_video_extensions": [".mp4", ".mov", ".mkv"],
            "target_audio_format": "wav",
            "target_audio_sample_rate": 16000,
            "target_audio_channels": 1,
            "target_video_format": "mp4",
            "extract_waveform": False,
            "extract_video_poster": False,
        },
        "retry": {
            "max_attempts": 1,
            "base_delay_seconds": 1,
            "max_delay_seconds": 1,
            "jitter_enabled": False,
        },
        "export": {
            "formats": ["json", "jsonl"],
            "include_review_metadata": True,
            "batch_naming_strategy": "timestamp",
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def test_autosave_submit_get_task_detail_review_flow(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source_sample = (
        Path(__file__).resolve().parents[2] / "media" / "1226-141268-0001.mp3"
    )
    shutil.copy2(source_sample, media_dir / source_sample.name)

    config_path = _write_test_config(tmp_path, media_dir)
    client = TestClient(create_app(str(config_path)))

    response = client.post("/api/media/import")
    response.raise_for_status()
    assert response.json()["imported"] == 1

    response = client.post("/api/media/preprocess")
    response.raise_for_status()
    assert response.json()["processed"] == 1

    response = client.get("/api/tasks/next", params={"annotator_id": "annotator_01"})
    response.raise_for_status()
    task_detail = response.json()
    task_id = task_detail["task"]["task_id"]

    autosave_payload = {
        "annotator_id": "annotator_01",
        "annotation": {
            "primary_emotion": "sad",
            "secondary_emotions": [],
            "intensity": 3,
            "confidence": 4,
            "valence": -0.4,
            "arousal": 2,
            "notes": "draft note",
        },
    }
    response = client.post(f"/api/tasks/{task_id}/autosave", json=autosave_payload)
    response.raise_for_status()
    autosaved = response.json()
    assert autosaved["task"]["status"] == "IN_PROGRESS"
    assert autosaved["latest_draft"] is not None
    assert autosaved["latest_draft"]["is_draft"] is True
    assert autosaved["latest_annotation"] is not None
    assert autosaved["latest_annotation"]["annotation"]["notes"] == "draft note"

    submit_payload = {
        "annotator_id": "annotator_01",
        "annotation": {
            "primary_emotion": "sad",
            "secondary_emotions": [],
            "intensity": 4,
            "confidence": 5,
            "valence": -0.6,
            "arousal": 3,
            "notes": "final note",
        },
    }
    response = client.post(f"/api/tasks/{task_id}/submit", json=submit_payload)
    response.raise_for_status()
    submitted = response.json()
    assert submitted["task"]["status"] == "SUBMITTED"
    assert submitted["latest_annotation"] is not None
    assert submitted["latest_annotation"]["is_draft"] is False
    assert submitted["latest_annotation"]["annotation"]["notes"] == "final note"
    # Backward compatibility for current frontend consumers.
    assert submitted["latest_draft"] is not None
    assert submitted["latest_draft"]["annotation"]["notes"] == "final note"

    response = client.get(f"/api/tasks/{task_id}")
    response.raise_for_status()
    detail = response.json()
    assert detail["task"]["status"] == "SUBMITTED"
    assert detail["latest_annotation"] is not None
    assert detail["latest_annotation"]["is_draft"] is False
    assert detail["latest_annotation"]["annotation"]["notes"] == "final note"
    assert detail["latest_draft"] is not None
    assert detail["latest_draft"]["annotation"]["notes"] == "final note"

    response = client.post(
        f"/api/reviews/{task_id}",
        json={"reviewer_id": "reviewer_01", "decision": "approved", "notes": "looks good"},
    )
    response.raise_for_status()
    review = response.json()
    assert review["task_id"] == task_id
    assert review["decision"] == "approved"

    response = client.get(f"/api/tasks/{task_id}")
    response.raise_for_status()
    reviewed_detail = response.json()
    assert reviewed_detail["task"]["status"] == "REVIEWED"
    assert reviewed_detail["latest_annotation"] is not None
    assert reviewed_detail["latest_annotation"]["annotation"]["notes"] == "final note"


def test_task_heartbeat_and_release_flow(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source_sample = (
        Path(__file__).resolve().parents[2] / "media" / "1250-135777-0085.mp3"
    )
    shutil.copy2(source_sample, media_dir / source_sample.name)

    config_path = _write_test_config(tmp_path, media_dir)
    client = TestClient(create_app(str(config_path)))

    client.post("/api/media/import").raise_for_status()
    client.post("/api/media/preprocess").raise_for_status()

    response = client.get("/api/tasks/next", params={"annotator_id": "annotator_01"})
    response.raise_for_status()
    acquired = response.json()
    task_id = acquired["task"]["task_id"]
    initial_lock_expires_at = acquired["task"]["lock_expires_at"]
    assert acquired["task"]["status"] == "IN_PROGRESS"

    response = client.post(
        f"/api/tasks/{task_id}/heartbeat",
        json={"annotator_id": "annotator_01", "reason": "active-editing"},
    )
    response.raise_for_status()
    heartbeated = response.json()
    assert heartbeated["task"]["status"] == "IN_PROGRESS"
    assert heartbeated["task"]["lock_expires_at"] > initial_lock_expires_at

    response = client.post(
        f"/api/tasks/{task_id}/release",
        json={"annotator_id": "annotator_01", "reason": "skip"},
    )
    response.raise_for_status()
    released = response.json()
    assert released["task"]["status"] == "READY"
    assert released["task"]["lock_expires_at"] is None
    assert released["task"]["assigned_to"] is None

    response = client.get("/api/tasks/next", params={"annotator_id": "annotator_01"})
    response.raise_for_status()
    reacquired = response.json()
    assert reacquired["task"]["task_id"] == task_id
