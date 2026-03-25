"""User tracking middleware — records authenticated user access to GAMA's Firestore."""
from __future__ import annotations

import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class UserTrackingMiddleware(BaseHTTPMiddleware):
    """Record authenticated user access on each API request.

    Fire-and-forget: tracking writes run in a background executor and never
    block or fail the response.
    """

    def __init__(self, app, *, service_name: str, gcp_project: str, auth_prefix: str):
        super().__init__(app)
        self.service_name = service_name
        self.gcp_project = gcp_project
        self.auth_prefix = auth_prefix

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only track authenticated API requests (skip health, static, auth endpoints).
        path = request.url.path
        if path.startswith("/api/") and not path.startswith(self.auth_prefix):
            try:
                from amaara_auth.dependencies import get_current_user

                user = get_current_user(request)
                if user:
                    from amaara_auth.tracking import record_access

                    loop = asyncio.get_running_loop()
                    loop.run_in_executor(
                        None, record_access, user.email, self.service_name, self.gcp_project
                    )
            except Exception:
                pass  # Never break a request over tracking.

        return response
