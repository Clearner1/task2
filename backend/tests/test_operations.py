from __future__ import annotations

import shutil
from pathlib import Path
import sys

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import task2_backend.domains.media.services as media_services_module
from task2_backend.common.enums import MediaType, TaskStatus
from task2_backend.common.exceptions import MediaDetectionError
from task2_backend.foundation.media_probe import MediaProbeResult
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
            "max_concurrent_jobs": 2,
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


def test_maintenance_replays_failed_preprocess_job_and_updates_ops_status(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source_sample = Path(__file__).resolve().parents[2] / "media" / "1226-141268-0001.mp3"
    shutil.copy2(source_sample, media_dir / source_sample.name)

    config_path = _write_test_config(tmp_path, media_dir)

    state = {"fail_probe": True}

    def fake_probe(path, audio_exts, video_exts):
        if state["fail_probe"]:
            raise MediaDetectionError(f"temporary probe failure for {path.name}", entity_id=path.name)
        return MediaProbeResult(
            media_type=MediaType.AUDIO,
            detected_format="mp3",
            duration_ms=14670,
            mime_type="audio/mpeg",
        )

    monkeypatch.setattr(media_services_module, "probe_media", fake_probe)

    with TestClient(create_app(str(config_path))) as client:
        response = client.post("/api/media/import")
        response.raise_for_status()
        assert response.json()["imported"] == 1

        response = client.post("/api/media/preprocess")
        response.raise_for_status()
        assert response.json() == {"processed": 0, "failed": 1}

        ops_before = client.get("/api/ops/status")
        ops_before.raise_for_status()
        assert ops_before.json()["pending_retry_jobs"] == 1
        assert ops_before.json()["terminal_failure_jobs"] == 0

        with client.app.state.database.connect() as connection:
            connection.execute(
                "UPDATE job_failures SET next_retry_at = ? WHERE job_name = ? AND entity_id = ?",
                ["2000-01-01T00:00:00+00:00", "media_preprocess", "1226-141268-0001"],
            )

        state["fail_probe"] = False
        summary = client.app.state.maintenance_runner.run_once()
        assert summary["resolved_retry_jobs"] == 1

        media = client.get("/api/media/1226-141268-0001")
        media.raise_for_status()
        assert media.json()["status"] == TaskStatus.PREPROCESSED.value

        task_detail = client.get("/api/tasks/next", params={"annotator_id": "annotator_01"})
        task_detail.raise_for_status()
        assert task_detail.json()["task"]["status"] == TaskStatus.IN_PROGRESS.value

        ops_after = client.get("/api/ops/status")
        ops_after.raise_for_status()
        snapshot = ops_after.json()
        assert snapshot["pending_retry_jobs"] == 0
        assert snapshot["media_status_counts"][TaskStatus.PREPROCESSED.value] == 1
        assert snapshot["task_status_counts"][TaskStatus.IN_PROGRESS.value] == 1
        assert snapshot["last_maintenance_run"]["status"] == "success"


def test_maintenance_reclaims_expired_task_lock(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source_sample = Path(__file__).resolve().parents[2] / "media" / "1250-135777-0085.mp3"
    shutil.copy2(source_sample, media_dir / source_sample.name)

    config_path = _write_test_config(tmp_path, media_dir)

    with TestClient(create_app(str(config_path))) as client:
        client.post("/api/media/import").raise_for_status()
        client.post("/api/media/preprocess").raise_for_status()

        task_detail = client.get("/api/tasks/next", params={"annotator_id": "annotator_01"})
        task_detail.raise_for_status()
        task_id = task_detail.json()["task"]["task_id"]

        with client.app.state.database.connect() as connection:
            connection.execute(
                "UPDATE annotation_tasks SET lock_expires_at = ? WHERE task_id = ?",
                ["2000-01-01T00:00:00+00:00", task_id],
            )

        before = client.get("/api/ops/status")
        before.raise_for_status()
        assert before.json()["stale_lock_count"] == 1

        summary = client.app.state.maintenance_runner.run_once()
        assert summary["reclaimed_expired_locks"] == 1

        detail = client.get(f"/api/tasks/{task_id}")
        detail.raise_for_status()
        payload = detail.json()
        assert payload["task"]["status"] == TaskStatus.READY.value
        assert payload["task"]["lock_expires_at"] is None
        assert payload["task"]["assigned_to"] is None

        after = client.get("/api/ops/status")
        after.raise_for_status()
        assert after.json()["stale_lock_count"] == 0
        assert after.json()["last_maintenance_run"]["summary"]["reclaimed_expired_locks"] == 1
