import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_env_path(env_file: str) -> Path:
    path = Path(env_file)
    return path if path.is_absolute() else BASE_DIR / path


def load_env() -> Path:
    """Load environment variables from the file specified by ENV_FILE (default .env)."""
    env_file = os.getenv("ENV_FILE", ".env")
    env_path = _resolve_env_path(env_file)
    load_dotenv(env_path, override=False)
    return env_path


