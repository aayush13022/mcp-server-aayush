# Google MCP Server

A FastAPI server that integrates with Google Docs and Gmail. Every action requires an explicit confirmation in the request before it runs, so nothing happens by accident — and this works both locally and when deployed.

## Features

- **Append to Google Doc** — append text to any document you have access to
- **Create Gmail draft** — create a draft email without sending it
- **OAuth 2.0** — credentials are saved locally after the first login
- **Approval gate** — every action requires `"confirm": true` in the request body. Without it, the server returns HTTP 428 with a preview and does nothing.
- **API-key auth** — when `API_KEY` is set, requests must include an `X-API-Key` header.

## Project Structure

```
google-mcp-server/
├── server.py          → FastAPI app with tool endpoints
├── auth.py            → Google OAuth authentication
├── docs_tool.py       → Google Docs tool (append content)
├── gmail_tool.py      → Gmail tool (create draft)
├── requirements.txt   → All dependencies
├── README.md          → Setup and usage instructions
├── credentials.json   → (NOT committed — downloaded from Google Cloud)
└── token.json         → (NOT committed — auto-generated after OAuth)
```

## Prerequisites

- Python 3.10+
- A Google Cloud project with the **Google Docs API** and **Gmail API** enabled

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (or select an existing one).
3. Enable these APIs:
   - [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com)
   - [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
4. Go to **APIs & Services → Credentials**.
5. Click **Create Credentials → OAuth client ID**.
6. Choose **Desktop app** as the application type.
7. Download the JSON file and save it as `credentials.json` in this directory.

## Installation

```bash
cd google-mcp-server
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## First-Time Authentication

On the first API call (or when you run the server and trigger an endpoint), a browser window opens for Google sign-in. After you approve, a `token.json` file is created automatically. Subsequent runs reuse that token and skip the browser flow.

To re-authenticate, delete `token.json` and restart the server.

## Running the Server

```bash
python server.py
```

Or with uvicorn directly:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server listens on `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

## Approval model

Every action endpoint requires an explicit `"confirm": true` field in the request body:

- **Without `confirm` (or `confirm: false`)** → the server returns **HTTP 428 (Precondition Required)** with a preview of the action and payload. Nothing is executed.
- **With `"confirm": true`** → the action runs.

This replaces the old terminal `y/n` prompt with an approval that works the same way locally and when deployed (e.g. on Railway, where there is no terminal). See `DEPLOYMENT_PLAN.md` for details.

## API Endpoints

> If `API_KEY` is configured, add `-H "X-API-Key: YOUR_API_KEY"` to every request below.

### POST /append_to_doc

Append text to a Google Doc.

**Request body:**

```json
{
  "doc_id": "YOUR_GOOGLE_DOC_ID",
  "content": "Text to append at the end of the document.\n",
  "confirm": true
}
```

The `doc_id` is the string between `/d/` and `/edit` in the document URL:

```
https://docs.google.com/document/d/ABC123xyz/edit
                                      ^^^^^^^^^^
                                      doc_id
```

**Example:**

```bash
curl -X POST http://localhost:8000/append_to_doc \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "ABC123xyz", "content": "Hello from the MCP server!\n", "confirm": true}'
```

If you omit `"confirm": true`, the server responds with HTTP 428 and a preview instead of running the action:

```json
{
  "detail": {
    "message": "Confirmation required for 'append_to_doc'. Resend the same request with \"confirm\": true to proceed.",
    "action": "append_to_doc",
    "payload": {"doc_id": "ABC123xyz", "content": "Hello from the MCP server!\n"}
  }
}
```

### POST /create_email_draft

Create a Gmail draft.

**Request body:**

```json
{
  "to": "recipient@example.com",
  "subject": "Draft subject line",
  "body": "Plain-text body of the email.",
  "confirm": true
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/create_email_draft \
  -H "Content-Type: application/json" \
  -d '{"to": "recipient@example.com", "subject": "Hello", "body": "This is a draft.", "confirm": true}'
```

The same `confirm` approval applies before the draft is created.

## OAuth Scopes

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/documents` | Read and edit Google Docs |
| `https://www.googleapis.com/auth/gmail.compose` | Create and manage Gmail drafts |

## Security Notes

- Never commit `credentials.json` or `token.json` — both are listed in `.gitignore`.
- Every action requires `"confirm": true`; requests without it return HTTP 428 and execute nothing.
- Set `API_KEY` in any shared/deployed environment so requests must carry a valid `X-API-Key` header.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Missing credentials.json` | Download OAuth credentials from Google Cloud and place the file in this directory. |
| `403 Access Not Configured` | Enable the Docs and Gmail APIs in your Google Cloud project. |
| Token expired / invalid | Delete `token.json` and re-authenticate. |
| Doc not found | Confirm the doc ID and that the signed-in account has edit access. |
| `428 Precondition Required` | Add `"confirm": true` to the request body to approve the action. |
| `401 Invalid or missing API key` | Include the `X-API-Key` header matching the server's `API_KEY`. |
