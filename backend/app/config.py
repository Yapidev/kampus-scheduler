from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "CampusFlow - Penjadwalan Kampus API"
    database_url: str = f"sqlite:///{(BASE_DIR / 'kampus_scheduler.db').as_posix()}"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    auto_seed: bool = True

    model_config = {"env_prefix": "KAMPUS_"}


settings = Settings()
