from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    novel_secret_key: str = "change-me-please-32-bytes-min"
    novel_access_token_ttl_min: int = 60
    novel_refresh_token_ttl_days: int = 14
    novel_cors_origins: str = "http://localhost:5173"

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_available_models: str = "gpt-4o,gpt-4o-mini,gpt-3.5-turbo"
    llm_max_tool_rounds: int = 10

    # Bootstrap admin
    novel_bootstrap_admin_email: str = "admin@novel.com"
    novel_bootstrap_admin_password: str = "admin123"
    novel_bootstrap_admin_name: str = "Admin"

    model_config = {"env_file": str(Path(__file__).resolve().parents[3] / ".env"), "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.novel_cors_origins.split(",") if o.strip()]

    @property
    def data_dir(self) -> Path:
        d = Path(__file__).resolve().parents[3] / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def db_path(self) -> Path:
        return self.data_dir / "novel_platform.db"

    @property
    def db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def available_models_list(self) -> list[str]:
        return [m.strip() for m in self.llm_available_models.split(",") if m.strip()]


settings = Settings()
