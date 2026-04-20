# Task2 Configuration

## Purpose

This document defines the runtime configuration surface for `task2`. Configuration is owned by the backend `foundation` layer and injected into domains as typed values.

## Source Precedence

1. checked-in default config file for local development
2. environment-specific config file
3. environment variables
4. command-line overrides

The resolved configuration must be validated once during application startup.

## Required Keys

### Paths

- `paths.input_dir`
- `paths.normalized_dir`
- `paths.export_dir`
- `paths.log_dir`
- `paths.database_path`
- `paths.temp_dir`

### Runtime

- `runtime.mode`
- `runtime.worker_enabled`
- `runtime.max_concurrent_jobs`
- `runtime.shutdown_grace_seconds`

### Annotation

- `annotation.autosave_interval_seconds`
- `annotation.heartbeat_interval_seconds`
- `annotation.task_lock_timeout_seconds`
- `annotation.allowed_primary_labels`
- `annotation.enable_secondary_labels`
- `annotation.enable_valence_arousal`

### Media

- `media.supported_audio_extensions`
- `media.supported_video_extensions`
- `media.target_audio_format`
- `media.target_audio_sample_rate`
- `media.extract_waveform`
- `media.extract_video_poster`

### Retry

- `retry.max_attempts`
- `retry.base_delay_seconds`
- `retry.max_delay_seconds`
- `retry.jitter_enabled`

### Export

- `export.formats`
- `export.include_review_metadata`
- `export.batch_naming_strategy`

## Rules

- Frontend may only consume presentation-safe configuration such as API base URL, feature flags, and display preferences.
- Backend domains must not read environment variables directly.
- New runtime knobs belong here before they are used in code.
- Every config key must map to an owner layer and at least one test.

## Suggested Initial Shape

```yaml
paths:
  input_dir: task2/media
  normalized_dir: task2/workspace/normalized
  export_dir: task2/exports
  log_dir: task2/logs
  database_path: task2/data/task2.db
  temp_dir: task2/workspace/tmp

runtime:
  mode: local
  worker_enabled: true
  max_concurrent_jobs: 2
  shutdown_grace_seconds: 30

annotation:
  autosave_interval_seconds: 15
  heartbeat_interval_seconds: 15
  task_lock_timeout_seconds: 300
  allowed_primary_labels: [neutral, happy, sad, angry, fear, surprise, disgust, other]
  enable_secondary_labels: true
  enable_valence_arousal: true

media:
  supported_audio_extensions: [.wav, .mp3, .flac, .m4a]
  supported_video_extensions: [.mp4, .mov, .mkv]
  target_audio_format: wav
  target_audio_sample_rate: 16000
  extract_waveform: true
  extract_video_poster: true

retry:
  max_attempts: 3
  base_delay_seconds: 1
  max_delay_seconds: 10
  jitter_enabled: true

export:
  formats: [json, jsonl]
  include_review_metadata: true
  batch_naming_strategy: timestamp
```
