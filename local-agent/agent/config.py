"""Local configuration storage for the Emboita Sync Agent.

Stored as a JSON file under the user's AppData folder (Windows) so settings
survive between runs and between rebuilds of the packaged .exe. This is the
"authentication config on the UI" for the local side — the Settings screen
in ui.py reads/writes exactly this file.
"""
import json
import os
from pathlib import Path

APP_DIR_NAME = "EmboitaSyncAgent"

DEFAULT_CONFIG = {
    "cloud_url": "http://localhost:8000",
    "api_key": "",
    "sync_interval_minutes": 5,
    "devices": [],  # [{"name": str, "ip": str, "port": int}, ...]
}


def get_app_dir() -> Path:
    base = os.getenv("APPDATA") or str(Path.home())
    app_dir = Path(base) / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_config_path() -> Path:
    return get_app_dir() / "config.json"


def get_db_path() -> Path:
    return get_app_dir() / "agent.sqlite3"


def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


def save_config(config: dict) -> None:
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
