"""amaara-auth — Google OAuth middleware for AmaaraNetworks FastAPI agents."""

from __future__ import annotations

from amaara_auth.config import AmaaraAuthSettings
from amaara_auth.dependencies import get_current_user, require_auth
from amaara_auth.router import create_auth_router
from amaara_auth.session import TokenData


def setup_auth(
    app: "FastAPI",
    settings: AmaaraAuthSettings,
    *,
    login_page_enabled: bool | None = None,
) -> None:
    """Wire Google OAuth into a FastAPI app.

    Call once during lifespan or at app creation time.

    Args:
        app: The FastAPI application instance.
        settings: Auth configuration (reads from env / .env).
        login_page_enabled: Override settings.login_page_enabled. Set False if
            the agent has its own frontend login screen (e.g. React SPA).
    """
    import logging
    import secrets

    logger = logging.getLogger(__name__)

    if not settings.session_secret_key:
        settings.session_secret_key = secrets.token_urlsafe(32)
        logger.warning("No SESSION_SECRET_KEY configured — using ephemeral key")

    app.state.auth_settings = settings
    app.state.oauth_sessions: dict = {}

    router = create_auth_router()
    app.include_router(router, prefix=settings.auth_prefix)

    enabled = login_page_enabled if login_page_enabled is not None else settings.login_page_enabled
    if enabled:
        from amaara_auth.login_page import create_login_route

        create_login_route(app, settings)


__all__ = [
    "setup_auth",
    "require_auth",
    "get_current_user",
    "AmaaraAuthSettings",
    "TokenData",
    "create_auth_router",
]
