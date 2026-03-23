from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from amaara_auth.config import AmaaraAuthSettings

LOGIN_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{app_name} — Sign In</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #04080f; color: #eef2f7; font-family: system-ui, -apple-system, sans-serif;
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
  }}
  .card {{
    background: #0b1a2e; border: 1px solid #1a3652; border-radius: 12px;
    padding: 2rem; max-width: 380px; width: 100%; text-align: center;
  }}
  h1 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; }}
  .subtitle {{ color: #8899aa; font-size: 0.875rem; margin-bottom: 1.5rem; }}
  .btn {{
    display: inline-block; width: 100%; padding: 0.625rem 1rem;
    background: #38b2f5; color: #fff; border-radius: 8px;
    font-weight: 500; text-decoration: none; font-size: 0.9375rem;
    transition: opacity 0.15s;
  }}
  .btn:hover {{ opacity: 0.9; }}
  .footer {{ color: #8899aa; font-size: 0.75rem; margin-top: 1rem; }}
</style>
</head>
<body>
  <div class="card">
    <h1>{app_name}</h1>
    <p class="subtitle">Sign in with your Amaara Networks account</p>
    <a href="{auth_prefix}/login" class="btn">Sign in with Google</a>
    <p class="footer">Restricted to @{allowed_domain}</p>
  </div>
</body>
</html>
"""


def create_login_route(app: FastAPI, settings: AmaaraAuthSettings) -> None:
    """Mount a built-in HTML login page at /login and a catch-all for unauthenticated access."""

    html = LOGIN_PAGE_TEMPLATE.format(
        app_name=settings.app_name,
        auth_prefix=settings.auth_prefix,
        allowed_domain=settings.allowed_domain,
    )

    @app.get("/login", include_in_schema=False)
    async def login_page(request: Request):
        return HTMLResponse(content=html)
