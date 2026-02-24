import json
import os
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "os-notif-telegram"


def get_config_path() -> Path:
    config_dir = Path(user_config_dir(APP_NAME))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def get_pid_path() -> Path:
    return Path(user_config_dir(APP_NAME)) / "forwarder.pid"


def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def is_configured(config: dict) -> bool:
    return bool(config.get("telegram_bot_token") and config.get("telegram_chat_id"))


def write_pid() -> None:
    get_pid_path().write_text(str(os.getpid()), encoding="utf-8")


def clear_pid() -> None:
    pid_path = get_pid_path()
    if pid_path.exists():
        pid_path.unlink()


def get_running_pid() -> int | None:
    """Return the PID of the running forwarder, or None if not running."""
    pid_path = get_pid_path()
    if not pid_path.exists():
        return None
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)  # signal 0 = just check if process exists
        return pid
    except (ProcessLookupError, PermissionError, ValueError, OSError):
        pid_path.unlink(missing_ok=True)
        return None
