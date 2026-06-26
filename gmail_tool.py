import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from auth import get_credentials


def _get_gmail_service():
    return build("gmail", "v1", credentials=get_credentials())


def create_email_draft(to: str, subject: str, body: str) -> dict:
    """Create a Gmail draft with the given recipient, subject, and body."""
    service = _get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    return (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
