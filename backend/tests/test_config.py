from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task2_backend.foundation.config import load_config


def test_load_config_uses_backend_config_file() -> None:
    config = load_config(str(Path(__file__).resolve().parents[1] / "config.yaml"))
    assert config.paths.input_dir.name == "media"
    assert config.annotation.task_lock_timeout_seconds == 300
