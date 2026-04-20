from __future__ import annotations

from array import array
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import wave

from task2_backend.common.enums import MediaType
from task2_backend.common.exceptions import MediaNormalizationError
from task2_backend.foundation.config import MediaConfig


@dataclass(frozen=True)
class MediaAssetBuildResult:
    asset_kind: str
    path: Path
    format: str
    sample_rate: int | None
    channels: int | None
    width: int | None
    height: int | None


@dataclass(frozen=True)
class MediaNormalizationResult:
    playable: MediaAssetBuildResult
    waveform: MediaAssetBuildResult | None = None
    poster: MediaAssetBuildResult | None = None


def normalize_media(
    *,
    source_path: Path,
    media_id: str,
    media_type: MediaType,
    config: MediaConfig,
    normalized_root: Path,
) -> MediaNormalizationResult:
    output_dir = normalized_root / media_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if media_type == MediaType.AUDIO:
        playable = _normalize_audio(source_path, output_dir, config)
        waveform = _generate_waveform(playable.path, output_dir) if config.extract_waveform else None
        return MediaNormalizationResult(playable=playable, waveform=waveform, poster=None)

    if media_type == MediaType.VIDEO:
        playable = _normalize_video(source_path, output_dir, config)
        poster = _generate_poster(source_path, output_dir) if config.extract_video_poster else None
        return MediaNormalizationResult(playable=playable, waveform=None, poster=poster)

    raise MediaNormalizationError(f"Unsupported media type for normalization: {media_type}", entity_id=source_path.name)


def _normalize_audio(source_path: Path, output_dir: Path, config: MediaConfig) -> MediaAssetBuildResult:
    target_ext = config.target_audio_format.lstrip(".")
    output_path = output_dir / f"playable.{target_ext}"
    codec = _audio_codec_for_format(target_ext)
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-ac",
            str(config.target_audio_channels),
            "-ar",
            str(config.target_audio_sample_rate),
            "-c:a",
            codec,
            str(output_path),
        ],
        source_path.name,
    )
    metadata = _probe_asset(output_path)
    return MediaAssetBuildResult(
        asset_kind="playable",
        path=output_path,
        format=metadata["format"],
        sample_rate=metadata["sample_rate"],
        channels=metadata["channels"],
        width=metadata["width"],
        height=metadata["height"],
    )


def _normalize_video(source_path: Path, output_dir: Path, config: MediaConfig) -> MediaAssetBuildResult:
    target_ext = config.target_video_format.lstrip(".")
    output_path = output_dir / f"playable.{target_ext}"
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ac",
            str(config.target_audio_channels),
            "-ar",
            str(config.target_audio_sample_rate),
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        source_path.name,
    )
    metadata = _probe_asset(output_path)
    return MediaAssetBuildResult(
        asset_kind="playable",
        path=output_path,
        format=metadata["format"],
        sample_rate=metadata["sample_rate"],
        channels=metadata["channels"],
        width=metadata["width"],
        height=metadata["height"],
    )


def _generate_poster(source_path: Path, output_dir: Path) -> MediaAssetBuildResult:
    output_path = output_dir / "poster.jpg"
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-vf",
            "thumbnail,scale=640:-1",
            "-frames:v",
            "1",
            str(output_path),
        ],
        source_path.name,
    )
    metadata = _probe_asset(output_path)
    return MediaAssetBuildResult(
        asset_kind="poster",
        path=output_path,
        format=metadata["format"],
        sample_rate=None,
        channels=None,
        width=metadata["width"],
        height=metadata["height"],
    )


def _generate_waveform(playable_audio_path: Path, output_dir: Path) -> MediaAssetBuildResult:
    output_path = output_dir / "waveform.json"
    peaks = _build_waveform_peaks(playable_audio_path)
    output_path.write_text(json.dumps({"peaks": peaks}, ensure_ascii=False), encoding="utf-8")
    metadata = _probe_asset(playable_audio_path)
    return MediaAssetBuildResult(
        asset_kind="waveform",
        path=output_path,
        format="json",
        sample_rate=metadata["sample_rate"],
        channels=metadata["channels"],
        width=None,
        height=None,
    )


def _build_waveform_peaks(audio_path: Path, bins: int = 64) -> list[float]:
    with wave.open(str(audio_path), "rb") as handle:
        frame_count = handle.getnframes()
        if frame_count == 0:
            return [0.0] * bins
        raw = handle.readframes(frame_count)
        sample_width = handle.getsampwidth()
        if sample_width != 2:
            raise MediaNormalizationError(
                f"Waveform generation expects 16-bit PCM audio, got sample width {sample_width}",
                entity_id=audio_path.name,
            )
        samples = array("h")
        samples.frombytes(raw)
        channels = max(handle.getnchannels(), 1)
        if channels > 1:
            mono = array("h")
            for index in range(0, len(samples), channels):
                mono.append(samples[index])
            samples = mono

    if len(samples) == 0:
        return [0.0] * bins

    chunk_size = max(len(samples) // bins, 1)
    peaks: list[float] = []
    max_value = float(2**15)
    for start in range(0, len(samples), chunk_size):
        chunk = samples[start:start + chunk_size]
        if len(chunk) == 0:
            peaks.append(0.0)
            continue
        peak = max(abs(value) for value in chunk) / max_value
        peaks.append(round(min(peak, 1.0), 4))
        if len(peaks) == bins:
            break
    while len(peaks) < bins:
        peaks.append(0.0)
    return peaks


def _probe_asset(path: Path) -> dict[str, int | str | None]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,sample_rate,channels,width,height:format=format_name",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout or "{}")
    except FileNotFoundError as exc:
        raise MediaNormalizationError("ffprobe is required for media normalization.") from exc
    except subprocess.CalledProcessError as exc:
        raise MediaNormalizationError(f"ffprobe failed for normalized asset {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise MediaNormalizationError(f"Invalid ffprobe output for normalized asset {path.name}") from exc

    streams = payload.get("streams", [])
    format_name = str(payload.get("format", {}).get("format_name", path.suffix.lstrip(".")))

    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)

    sample_rate = int(audio_stream["sample_rate"]) if audio_stream and audio_stream.get("sample_rate") else None
    channels = int(audio_stream["channels"]) if audio_stream and audio_stream.get("channels") else None
    width = int(video_stream["width"]) if video_stream and video_stream.get("width") else None
    height = int(video_stream["height"]) if video_stream and video_stream.get("height") else None

    return {
        "format": format_name.split(",")[0],
        "sample_rate": sample_rate,
        "channels": channels,
        "width": width,
        "height": height,
    }


def _audio_codec_for_format(target_ext: str) -> str:
    codecs = {
        "wav": "pcm_s16le",
        "flac": "flac",
        "mp3": "libmp3lame",
        "m4a": "aac",
        "aac": "aac",
    }
    return codecs.get(target_ext, "pcm_s16le")


def _run_ffmpeg(command: list[str], entity_id: str) -> None:
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise MediaNormalizationError("ffmpeg is required for media normalization.", entity_id=entity_id) from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "ffmpeg failed"
        raise MediaNormalizationError(message, entity_id=entity_id) from exc
