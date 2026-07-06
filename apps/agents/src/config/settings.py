# apps/agents/src/config/settings.py

from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_model: str = "local-model"
    llm_temperature: float = 0.2

    workspace_root: Path = PROJECT_ROOT / "workspace"

    max_tree_depth: int = 2
    max_tree_entries: int = 200
    max_key_files: int = 5
    max_file_chars: int = 12000

    class Config:
        env_file = ".env"


settings = Settings()