from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AmaaraAuthSettings(BaseSettings):
    """OAuth settings for AmaaraNetworks agents.

    Can be used standalone or composed into an agent's own settings class.
    All fields read from environment variables / .env by default.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    session_secret_key: str = ""
    allowed_domain: str = "amaaranetworks.com"
    session_max_age: int = 7 * 24 * 3600  # 1 week
    auth_prefix: str = "/api/v1/auth"
    app_name: str = "Amaara Networks"
    login_page_enabled: bool = True
    cookie_prefix: str = "amaara"  # yields amaara_session, amaara_oauth_state
