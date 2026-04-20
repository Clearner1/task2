from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task2_backend.foundation.config import load_config
from task2_backend.foundation.database import Database
from task2_backend.domains.annotation.repository import AnnotationRepository
from task2_backend.domains.annotation.services import AnnotationService
from task2_backend.domains.media.repository import MediaRepository
from task2_backend.domains.media.services import MediaService


def test_import_media_is_idempotent(tmp_path) -> None:
    input_dir = tmp_path / "media"
    input_dir.mkdir()
    sample = input_dir / "sample.mp3"
    sample.write_bytes(b"fake")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
paths:
  input_dir: ./media
  normalized_dir: ./workspace/normalized
  export_dir: ./exports
  log_dir: ./logs
  database_path: ./data/task2.db
  temp_dir: ./workspace/tmp
runtime:
  mode: test
  worker_enabled: true
  max_concurrent_jobs: 1
  shutdown_grace_seconds: 5
annotation:
  autosave_interval_seconds: 15
  heartbeat_interval_seconds: 15
  task_lock_timeout_seconds: 300
  allowed_primary_labels: [neutral, happy]
  enable_secondary_labels: true
  enable_valence_arousal: true
media:
  supported_audio_extensions: [.mp3]
  supported_video_extensions: [.mp4]
  target_audio_format: wav
  target_audio_sample_rate: 16000
  extract_waveform: false
  extract_video_poster: false
retry:
  max_attempts: 1
  base_delay_seconds: 1
  max_delay_seconds: 1
  jitter_enabled: false
export:
  formats: [json]
  include_review_metadata: true
  batch_naming_strategy: timestamp
        """.strip(),
        encoding="utf-8",
    )
    config = load_config(str(config_path))
    database = Database(config.paths.database_path)
    database.init_schema()

    media_service = MediaService(config, MediaRepository(database))
    annotation_service = AnnotationService(config, AnnotationRepository(database))
    first = media_service.import_media()
    annotation_service.sync_from_media()
    second = media_service.import_media()
    annotation_service.sync_from_media()

    assert first.imported == 1
    assert second.existing == 1
