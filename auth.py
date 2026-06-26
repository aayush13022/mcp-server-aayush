import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose",
]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def is_production() -> bool:
    """True when running on Railway or when forced via APP_ENV."""
    return os.getenv("APP_ENV") == "production" or bool(
        os.getenv("RAILWAY_ENVIRONMENT")
    )


def _load_token() -> Credentials | None:
    """Load credentials from the GOOGLE_TOKEN_JSON env var or token.json file."""
    raw = os.getenv("GOOGLE_TOKEN_JSON")
    if raw:
        return Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    if TOKEN_FILE.exists():
        return Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    return None


def _run_oauth_flow() -> Credentials:
    """Run the interactive browser OAuth flow (local/dev only)."""
    raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if raw:
        flow = InstalledAppFlow.from_client_config(json.loads(raw), SCOPES)
    else:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Missing {CREDENTIALS_FILE}. "
                "Download OAuth credentials from Google Cloud Console "
                "or set GOOGLE_CREDENTIALS_JSON."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )
    return flow.run_local_server(port=0)


def _persist_token(creds: Credentials) -> None:
    """Save the token to disk. Best-effort on Railway's ephemeral filesystem."""
    try:
        TOKEN_FILE.write_text(creds.to_json())
    except OSError:
        pass


def get_credentials() -> Credentials:
    """Return valid Google API credentials.

    In production, credentials come from environment variables and are
    refreshed headlessly. The interactive browser flow only runs locally.
    """
    creds = _load_token()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _persist_token(creds)
        return creds

    if is_production():
        raise RuntimeError(
            "No valid Google credentials available. Set a valid "
            "GOOGLE_TOKEN_JSON environment variable (generate token.json "
            "locally first). Interactive OAuth is disabled in production."
        )

    creds = _run_oauth_flow()
    _persist_token(creds)
    return creds
