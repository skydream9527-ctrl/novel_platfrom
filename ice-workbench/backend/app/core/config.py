"""Application settings, sourced from .env at repo root."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT_DEFAULT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    DATA_ROOT: Path = REPO_ROOT_DEFAULT
    ICE_SECRET_KEY: str = "dev-secret-please-change-me-32bytes"
    ICE_ACCESS_TOKEN_TTL_MIN: int = 60
    ICE_REFRESH_TOKEN_TTL_DAYS: int = 14
    ICE_CORS_ORIGINS: str = "http://localhost:5173"

    # LLM gateway — OpenAI-compatible. Preferred path.
    MIFY_GATEWAY_BASE_URL: str = ""
    MIFY_GATEWAY_API_KEY: str = ""
    MIFY_DEFAULT_MODEL: str = "ppio/pa/claude-opus-4-7"

    # LLM (legacy native Anthropic SDK fallback)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-opus-4-7"
    ANTHROPIC_BASE_URL: str = ""

    # Feishu OAuth (standard open platform OR Xiaomi internal Lark variant).
    # `FEISHU_HOST` lets you point at the internal domain when Xiaomi Lark
    # exposes the same OAuth endpoints under a different hostname.
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_HOST: str = "https://open.feishu.cn"
    FEISHU_REDIRECT_URI: str = "http://localhost:5173/auth/feishu/callback"

    # Kyuubi (Xiaomi internal SQL gateway). Defaults bundled for chnbj/iceberg.
    KYUUBI_HOST: str = ""
    KYUUBI_PORT: int = 10009
    KYUUBI_USER: str = ""
    KYUUBI_PASSWORD: str = ""
    KYUUBI_REGION: str = "chnbj"
    KYUUBI_WORKSPACE: str = "11329"
    KYUUBI_CATALOG: str = "iceberg_zjyprc_hadoop"
    KYUUBI_ENGINE: str = "presto"
    KYUUBI_TOKEN: str = ""

    # Bootstrap admin
    ICE_BOOTSTRAP_ADMIN_EMAIL: str = "admin"
    ICE_BOOTSTRAP_ADMIN_PASSWORD: str = "admin123"
    ICE_BOOTSTRAP_ADMIN_NAME: str = "系统管理员"

    # 米盾 (Aegis) — production auth. When enabled, JWT is replaced by
    # X-Proxy-UserDetail header verification. Public key from the Aegis admin
    # console; multi-key is supported (comma-separated). Local dev can set
    # AEGIS_DEV_BYPASS_EMAIL to fake a user without going through the proxy.
    AEGIS_ENABLED: bool = True
    AEGIS_PUBLIC_KEY: str = ""           # comma-separated; PEM or base64 DER
    AEGIS_ADMIN_EMAILS: str = ""         # comma-separated → auth_role=super_admin
    AEGIS_DEV_BYPASS_EMAIL: str = ""     # local dev only; non-empty disables verification

    @field_validator("DATA_ROOT", mode="before")
    @classmethod
    def _resolve_data_root(cls, v):
        """Empty string / '.' / missing -> repo root. Makes the bundle
        portable: another machine can `unzip && make dev` without editing .env."""
        if v in ("", ".", None):
            return REPO_ROOT_DEFAULT
        # Relative path: resolve against the repo root, not cwd.
        from pathlib import Path as _P

        p = _P(str(v)).expanduser()
        if not p.is_absolute():
            p = (REPO_ROOT_DEFAULT / p).resolve()
        return p

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.ICE_CORS_ORIGINS.split(",") if s.strip()]

    @property
    def aegis_public_keys(self) -> list[str]:
        return [s.strip() for s in self.AEGIS_PUBLIC_KEY.split(",") if s.strip()]

    @property
    def aegis_admin_emails(self) -> set[str]:
        return {s.strip().lower() for s in self.AEGIS_ADMIN_EMAILS.split(",") if s.strip()}

    @property
    def cache_dir(self) -> Path:
        d = self.DATA_ROOT / ".cache"
        d.mkdir(exist_ok=True)
        return d

    @property
    def cache_db_path(self) -> Path:
        return self.cache_dir / "index.db"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.MIFY_GATEWAY_API_KEY) or bool(self.ANTHROPIC_API_KEY)

    @property
    def gateway_enabled(self) -> bool:
        return bool(self.MIFY_GATEWAY_BASE_URL and self.MIFY_GATEWAY_API_KEY)

    @property
    def feishu_enabled(self) -> bool:
        return bool(self.FEISHU_APP_ID and self.FEISHU_APP_SECRET)

    @property
    def kyuubi_enabled(self) -> bool:
        import shutil
        return bool(self.KYUUBI_TOKEN) and shutil.which("kyuubi") is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
