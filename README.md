# Google MCP Server

A FastAPI server that integrates with Google Docs and Gmail. Before each action runs, it prints the action and payload to the terminal and waits for your approval.

## Features

- **Append to Google Doc** — append text to any document you have access to
- **Create Gmail draft** — create a draft email without sending it
- **OAuth 2.0** — credentials are saved locally after the first login
- **Approval gate** — every request requires `y` in the terminal before execution

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

Run in the foreground so you can see approval prompts in the terminal:

```bash
python server.py
```

Or with uvicorn directly:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server listens on `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

## API Endpoints

### POST /append_to_doc

Append text to a Google Doc.

**Request body:**

```json
{
  "doc_id": "YOUR_GOOGLE_DOC_ID",
  "content": "Text to append at the end of the document.\n"
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
  -d '{"doc_id": "ABC123xyz", "content": "Hello from the MCP server!\n"}'
```

The terminal shows the action and payload, then prompts:

```
Action: append_to_doc
Payload: {'doc_id': 'ABC123xyz', 'content': 'Hello from the MCP server!\n'}
Approve? (y/n):
```

Type `y` to proceed or anything else to reject (returns HTTP 403).

### POST /create_email_draft

Create a Gmail draft.

**Request body:**

```json
{
  "to": "recipient@example.com",
  "subject": "Draft subject line",
  "body": "Plain-text body of the email."
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/create_email_draft \
  -H "Content-Type: application/json" \
  -d '{"to": "recipient@example.com", "subject": "Hello", "body": "This is a draft."}'
```

Same approval prompt applies before the draft is created.

## OAuth Scopes

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/documents` | Read and edit Google Docs |
| `https://www.googleapis.com/auth/gmail.compose` | Create and manage Gmail drafts |

## Security Notes

- Never commit `credentials.json` or `token.json` — both are listed in `.gitignore`.
- The approval prompt runs in the server terminal; keep the server in the foreground when testing.
- Rejecting an action returns HTTP 403 with `"Action rejected by user"`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Missing credentials.json` | Download OAuth credentials from Google Cloud and place the file in this directory. |
| `403 Access Not Configured` | Enable the Docs and Gmail APIs in your Google Cloud project. |
| Token expired / invalid | Delete `token.json` and re-authenticate. |
| Doc not found | Confirm the doc ID and that the signed-in account has edit access. |
| Approval prompt not visible | Run the server in a terminal (not as a background daemon). |
