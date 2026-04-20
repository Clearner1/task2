from __future__ import annotations

import shutil
from pathlib import Path
import sys

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task2_backend.common.enums import TaskStatus
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
            "extract_waveform": True,
            "extract_video_poster": False,
        },
        "retry": {
            "max_attempts": 1,
            "base_delay_seconds": 1,
            "max_delay_seconds": 1,
            "jitter_enabled": False,
        },
        "export": {
            "formats": ["json"],
            "include_review_metadata": True,
            "batch_naming_strategy": "timestamp",
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def test_audio_preprocess_generates_deterministic_normalized_assets(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source_sample = Path(__file__).resolve().parents[2] / "media" / "1226-141268-0001.mp3"
    shutil.copy2(source_sample, media_dir / source_sample.name)

    config_path = _write_test_config(tmp_path, media_dir)

    with TestClient(create_app(str(config_path))) as client:
        client.post("/api/media/import").raise_for_status()
        response = client.post("/api/media/preprocess")
        response.raise_for_status()
        assert response.json() == {"processed": 1, "failed": 0}

        media = client.get("/api/media/1226-141268-0001")
        media.raise_for_status()
        payload = media.json()
        assert payload["status"] == TaskStatus.PREPROCESSED.value
        assert payload["playable_asset_url"] == "/api/media/1226-141268-0001/stream"
        assert payload["waveform_url"] == "/api/media/1226-141268-0001/waveform"
        assert payload["poster_url"] is None
        assert len(payload["assets"]) == 2

        playable = next(asset for asset in payload["assets"] if asset["asset_kind"] == "playable")
        waveform = next(asset for asset in payload["assets"] if asset["asset_kind"] == "waveform")
        assert playable["path"].endswith("/1226-141268-0001/playable.wav")
        assert playable["format"] == "wav"
        assert playable["sample_rate"] == 16000
        assert playable["channels"] == 1
        assert waveform["path"].endswith("/1226-141268-0001/waveform.json")

        waveform_response = client.get("/api/media/1226-141268-0001/waveform")
        waveform_response.raise_for_status()
        waveform_payload = waveform_response.json()
        assert len(waveform_payload["peaks"]) == 64

        normalized_path = client.app.state.media_service.get_stream_path("1226-141268-0001")
        assert normalized_path is not None
        assert normalized_path.name == "playable.wav"

        with client.app.state.database.connect() as connection:
            connection.execute("DELETE FROM media_assets WHERE media_id = ?", ["1226-141268-0001"])

        replay = client.post("/api/media/preprocess")
        replay.raise_for_status()
        assert replay.json() == {"processed": 1, "failed": 0}

        media_after = client.get("/api/media/1226-141268-0001")
        media_after.raise_for_status()
        payload_after = media_after.json()
        playable_after = next(asset for asset in payload_after["assets"] if asset["asset_kind"] == "playable")
        waveform_after = next(asset for asset in payload_after["assets"] if asset["asset_kind"] == "waveform")
        assert playable_after["path"] == playable["path"]
        assert waveform_after["path"] == waveform["path"]
