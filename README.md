# amaara-auth

Google OAuth middleware for AmaaraNetworks FastAPI agents. Drop-in authentication restricted to @amaaranetworks.com.

## Install

```bash
pip install git+https://github.com/AmaaraNetworks/amaara-auth.git@v0.1.0
```

Or in `requirements.txt`:

```
amaara-auth @ git+https://github.com/AmaaraNetworks/amaara-auth.git@v0.1.0
```

## Quick Start

```python
from fastapi import FastAPI
from amaara_auth import setup_auth, AmaaraAuthSettings, require_auth

app = FastAPI()
setup_auth(app, AmaaraAuthSettings())
```

That's it. This gives you:
- `/api/v1/auth/login` — Google OAuth login
- `/api/v1/auth/callback` — OAuth callback
- `/api/v1/auth/status` — Check auth status
- `/api/v1/auth/logout` — Clear session
- `/login` — Built-in HTML login page

### Protect your routes

```python
from fastapi import APIRouter, Depends
from amaara_auth import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "authenticated"}
```

## Configuration

All settings read from environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_OAUTH_CLIENT_ID` | `""` | Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `""` | Google OAuth client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/callback` | OAuth callback URL |
| `SESSION_SECRET_KEY` | `""` (auto-generated) | Signed cookie secret |
| `ALLOWED_DOMAIN` | `amaaranetworks.com` | Google Workspace domain restriction |
| `APP_NAME` | `Amaara Networks` | Shown on built-in login page |
| `COOKIE_PREFIX` | `amaara` | Cookie name prefix (e.g. `amaara_session`) |
| `LOGIN_PAGE_ENABLED` | `true` | Set `false` if agent has its own login UI |

## For agents with custom frontends (e.g. React SPA)

```python
setup_auth(app, settings, login_page_enabled=False)
```

Then handle the login screen in your frontend — just link to `/api/v1/auth/login`.
