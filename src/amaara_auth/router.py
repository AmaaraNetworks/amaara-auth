from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from amaara_auth.dependencies import get_current_user
from amaara_auth.session import (
    TokenData,
    get_cookie_names,
    get_serializer,
    get_session_id,
    get_session_store,
)

logger = logging.getLogger(__name__)


def create_auth_router() -> APIRouter:
    """Create the auth APIRouter with login, callback, status, and logout endpoints."""

    router = APIRouter()

    @router.get("/login")
    async def login(request: Request):
        """Redirect user to Google OAuth consent screen."""
        from google_auth_oauthlib.flow import Flow

        settings = request.app.state.auth_settings
        if not settings.google_oauth_client_id:
            return {"error": "OAuth not configured"}

        state = secrets.token_urlsafe(32)

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
            redirect_uri=settings.google_oauth_redirect_uri,
        )

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="select_account",
            state=state,
            hd=settings.allowed_domain,
        )

        cookie_data = {"state": state, "code_verifier": flow.code_verifier}

        _, state_cookie = get_cookie_names(request)
        response = RedirectResponse(url=auth_url)
        serializer = get_serializer(request)
        response.set_cookie(
            state_cookie,
            serializer.dumps(cookie_data),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=600,
        )
        return response

    @router.get("/callback")
    async def callback(request: Request, code: str, state: str):
        """Handle OAuth callback from Google."""
        from google_auth_oauthlib.flow import Flow

        settings = request.app.state.auth_settings
        _, state_cookie_name = get_cookie_names(request)

        serializer = get_serializer(request)
        state_cookie = request.cookies.get(state_cookie_name)
        if not state_cookie:
            return RedirectResponse(url="/?auth_error=missing_state")
        try:
            cookie_data = serializer.loads(state_cookie, max_age=600)
        except Exception:
            return RedirectResponse(url="/?auth_error=invalid_state")

        expected_state = cookie_data["state"]
        code_verifier = cookie_data.get("code_verifier")

        if state != expected_state:
            return RedirectResponse(url="/?auth_error=state_mismatch")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
            redirect_uri=settings.google_oauth_redirect_uri,
        )
        flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user email and verify domain.
        email = ""
        try:
            from google.auth.transport.requests import Request as GoogleRequest
            from google.oauth2 import id_token

            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                GoogleRequest(),
                settings.google_oauth_client_id,
            )
            email = id_info.get("email", "")
            hosted_domain = id_info.get("hd", "")

            if settings.allowed_domain and hosted_domain != settings.allowed_domain:
                logger.warning("Domain mismatch: %s (expected %s)", hosted_domain, settings.allowed_domain)
                return RedirectResponse(url="/?auth_error=domain_mismatch")
        except Exception:
            logger.warning("Could not extract email from ID token")
            return RedirectResponse(url="/?auth_error=token_error")

        session_id = secrets.token_urlsafe(32)
        store = get_session_store(request)
        store[session_id] = TokenData(
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expiry=credentials.expiry,
            email=email,
        )

        session_cookie_name, _ = get_cookie_names(request)
        response = RedirectResponse(url="/")
        response.set_cookie(
            session_cookie_name,
            serializer.dumps(session_id),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.session_max_age,
        )
        response.delete_cookie(state_cookie_name)
        return response

    @router.get("/status")
    async def auth_status(request: Request):
        """Check if user is authenticated."""
        user = get_current_user(request)
        if not user:
            return {"logged_in": False}
        return {"logged_in": True, "email": user.email}

    @router.post("/logout")
    async def logout(request: Request):
        """Clear user session."""
        session_id = get_session_id(request)
        if session_id:
            store = get_session_store(request)
            store.pop(session_id, None)

        session_cookie_name, _ = get_cookie_names(request)
        response = RedirectResponse(url="/", status_code=303)
        response.delete_cookie(session_cookie_name)
        return response

    return router
