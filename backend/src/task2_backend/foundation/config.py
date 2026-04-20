from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any

import yaml

from task2_backend.common.exceptions import ConfigValidationError


@dataclass(frozen=True)
class PathsConfig:
    input_dir: Path
    normalized_dir: Path
    export_dir: Path
    log_dir: Path
    database_path: Path
    temp_dir: Path


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    worker_enabled: bool
    maintenance_interval_seconds: int
    max_concurrent_jobs: int
    shutdown_grace_seconds: int


@dataclass(frozen=True)
class AnnotationConfig:
    autosave_interval_seconds: int
    heartbeat_interval_seconds: int
    task_lock_timeout_seconds: int
    allowed_primary_labels: tuple[str, ...]
    enable_secondary_labels: bool
    enable_valence_arousal: bool


@dataclass(frozen=True)
class MediaConfig:
    supported_audio_extensions: tuple[str, ...]
    supported_video_extensions: tuple[str, ...]
    target_audio_format: str
    target_audio_sample_rate: int
    target_audio_channels: int
    target_video_format: str
    extract_waveform: bool
    extract_video_poster: bool


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int
    base_delay_seconds: int
    max_delay_seconds: int
    jitter_enabled: bool


@dataclass(frozen=True)
class ExportConfig:
    formats: tuple[str, ...]
    include_review_metadata: bool
    batch_naming_strategy: str


@dataclass(frozen=True)
class AppConfig:
    paths: PathsConfig
    runtime: RuntimeConfig
    annotation: AnnotationConfig
    media: MediaConfig
    retry: RetryConfig
    export: ExportConfig


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigValidationError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ConfigValidationError("Config root must be a mapping.")
    return loaded


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigValidationError(f"Missing config key: {key}")
    return mapping[key]


def load_config(config_path: str | None = None) -> AppConfig:
    env_config = os.getenv("TASK2_CONFIG_PATH")
    raw_path = config_path or env_config or "config.yaml"
    path = Path(raw_path).resolve()
    config_dir = path.parent
    raw = _load_yaml(path)

    paths = raw.get("paths", {})
    runtime = raw.get("runtime", {})
    annotation = raw.get("annotation", {})
    media = raw.get("media", {})
    retry = raw.get("retry", {})
    export = raw.get("export", {})

    resolved = AppConfig(
        paths=PathsConfig(
            input_dir=_resolve_path(config_dir, _require(paths, "input_dir")),
            normalized_dir=_resolve_path(config_dir, _require(paths, "normalized_dir")),
            export_dir=_resolve_path(config_dir, _require(paths, "export_dir")),
            log_dir=_resolve_path(config_dir, _require(paths, "log_dir")),
            database_path=_resolve_path(config_dir, _require(paths, "database_path")),
            temp_dir=_resolve_path(config_dir, _require(paths, "temp_dir")),
        ),
        runtime=RuntimeConfig(
            mode=str(_require(runtime, "mode")),
            worker_enabled=bool(_require(runtime, "worker_enabled")),
            maintenance_interval_seconds=int(_require(runtime, "maintenance_interval_seconds")),
            max_concurrent_jobs=int(_require(runtime, "max_concurrent_jobs")),
            shutdown_grace_seconds=int(_require(runtime, "shutdown_grace_seconds")),
        ),
        annotation=AnnotationConfig(
            autosave_interval_seconds=int(_require(annotation, "autosave_interval_seconds")),
            heartbeat_interval_seconds=int(_require(annotation, "heartbeat_interval_seconds")),
            task_lock_timeout_seconds=int(_require(annotation, "task_lock_timeout_seconds")),
            allowed_primary_labels=tuple(str(item) for item in _require(annotation, "allowed_primary_labels")),
            enable_secondary_labels=bool(_require(annotation, "enable_secondary_labels")),
            enable_valence_arousal=bool(_require(annotation, "enable_valence_arousal")),
        ),
        media=MediaConfig(
            supported_audio_extensions=tuple(str(item).lower() for item in _require(media, "supported_audio_extensions")),
            supported_video_extensions=tuple(str(item).lower() for item in _require(media, "supported_video_extensions")),
            target_audio_format=str(_require(media, "target_audio_format")),
            target_audio_sample_rate=int(_require(media, "target_audio_sample_rate")),
            target_audio_channels=int(_require(media, "target_audio_channels")),
            target_video_format=str(_require(media, "target_video_format")),
            extract_waveform=bool(_require(media, "extract_waveform")),
            extract_video_poster=bool(_require(media, "extract_video_poster")),
        ),
        retry=RetryConfig(
            max_attempts=int(_require(retry, "max_attempts")),
            base_delay_seconds=int(_require(retry, "base_delay_seconds")),
            max_delay_seconds=int(_require(retry, "max_delay_seconds")),
            jitter_enabled=bool(_require(retry, "jitter_enabled")),
        ),
        export=ExportConfig(
            formats=tuple(str(item) for item in _require(export, "formats")),
            include_review_metadata=bool(_require(export, "include_review_metadata")),
            batch_naming_strategy=str(_require(export, "batch_naming_strategy")),
        ),
    )
    ensure_runtime_paths(resolved)
    return resolved


def ensure_runtime_paths(config: AppConfig) -> None:
    config.paths.normalized_dir.mkdir(parents=True, exist_ok=True)
    config.paths.export_dir.mkdir(parents=True, exist_ok=True)
    config.paths.log_dir.mkdir(parents=True, exist_ok=True)
    config.paths.database_path.parent.mkdir(parents=True, exist_ok=True)
    config.paths.temp_dir.mkdir(parents=True, exist_ok=True)
