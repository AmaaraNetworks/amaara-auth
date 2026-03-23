from __future__ import annotations

from fastapi import HTTPException, Request

from amaara_auth.session import TokenData, get_session_id, get_session_store


def get_current_user(request: Request) -> TokenData | None:
    """Get current authenticated user, or None."""
    session_id = get_session_id(request)
    if not session_id:
        return None
    store = get_session_store(request)
    return store.get(session_id)


def require_auth(request: Request) -> TokenData:
    """FastAPI dependency that requires authentication. Raises 401 if not logged in."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
