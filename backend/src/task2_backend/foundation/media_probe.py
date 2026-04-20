from __future__ import annotations

from dataclasses import dataclass
import json
import mimetypes
from pathlib import Path
import subprocess

from task2_backend.common.enums import MediaType
from task2_backend.common.exceptions import MediaDetectionError, UnsupportedMediaFormatError


@dataclass(frozen=True)
class MediaProbeResult:
    media_type: MediaType
    detected_format: str
    duration_ms: int
    mime_type: str


def infer_media_type(path: Path, audio_exts: tuple[str, ...], video_exts: tuple[str, ...]) -> MediaType:
    suffix = path.suffix.lower()
    if suffix in audio_exts:
        return MediaType.AUDIO
    if suffix in video_exts:
        return MediaType.VIDEO
    return MediaType.UNKNOWN


def probe_media(path: Path, audio_exts: tuple[str, ...], video_exts: tuple[str, ...]) -> MediaProbeResult:
    media_type = infer_media_type(path, audio_exts, video_exts)
    if media_type == MediaType.UNKNOWN:
        raise UnsupportedMediaFormatError(f"Unsupported media extension: {path.suffix}", entity_id=path.name)

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,format_name",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout or "{}")
        fmt = payload.get("format", {})
        duration = float(fmt.get("duration", 0) or 0)
        detected_format = str(fmt.get("format_name", path.suffix.lstrip(".")))
        mime_type, _ = mimetypes.guess_type(path.name)
        return MediaProbeResult(
            media_type=media_type,
            detected_format=detected_format,
            duration_ms=int(duration * 1000),
            mime_type=mime_type or "application/octet-stream",
        )
    except subprocess.CalledProcessError as exc:
        raise MediaDetectionError(f"ffprobe failed for {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise MediaDetectionError(f"Invalid ffprobe output for {path.name}") from exc
