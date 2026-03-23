from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fastapi import Request
from itsdangerous import URLSafeTimedSerializer


@dataclass
class TokenData:
    """OAuth token data for a single user session."""

    access_token: str
    refresh_token: str | None
    expiry: datetime | None
    email: str


def get_session_store(request: Request) -> dict[str, TokenData]:
    return request.app.state.oauth_sessions


def get_serializer(request: Request) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(request.app.state.auth_settings.session_secret_key)


def get_cookie_names(request: Request) -> tuple[str, str]:
    """Return (session_cookie, state_cookie) names based on configured prefix."""
    prefix = request.app.state.auth_settings.cookie_prefix
    return f"{prefix}_session", f"{prefix}_oauth_state"


def get_session_id(request: Request) -> str | None:
    """Extract and validate session ID from cookie."""
    session_cookie, _ = get_cookie_names(request)
    cookie = request.cookies.get(session_cookie)
    if not cookie:
        return None
    try:
        max_age = request.app.state.auth_settings.session_max_age
        serializer = get_serializer(request)
        return serializer.loads(cookie, max_age=max_age)
    except Exception:
        return None
