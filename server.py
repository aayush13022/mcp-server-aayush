import os

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from auth import is_production
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

app = FastAPI(title="Google MCP Server", version="1.0.0")

API_KEY = os.getenv("API_KEY")


class AppendToDocRequest(BaseModel):
    doc_id: str
    content: str


class CreateEmailDraftRequest(BaseModel):
    to: str
    subject: str
    body: str


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Enforce the X-API-Key header.

    In production an API key MUST be configured; if it is missing we refuse
    all requests. In local dev with no key set, requests are allowed.
    """
    if not API_KEY:
        if is_production():
            raise HTTPException(status_code=503, detail="API_KEY not configured")
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def approve_action(action_name: str, payload: dict) -> bool:
    """Approve an action.

    In production (headless) actions are auto-approved once the API key has
    been validated. Locally, prompt for interactive terminal confirmation.
    """
    if is_production():
        print(f"\nAction: {action_name}")
        print(f"Payload: {payload}")
        print("Auto-approved (production mode).")
        return True

    print(f"\nAction: {action_name}")
    print(f"Payload: {payload}")
    response = input("Approve? (y/n): ").strip().lower()
    return response == "y"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/append_to_doc")
def append_to_doc_endpoint(
    request: AppendToDocRequest, _: None = Depends(require_api_key)
):
    payload = request.model_dump()
    if not approve_action("append_to_doc", payload):
        raise HTTPException(status_code=403, detail="Action rejected by user")

    try:
        result = append_to_doc(request.doc_id, request.content)
        return {"status": "success", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/create_email_draft")
def create_email_draft_endpoint(
    request: CreateEmailDraftRequest, _: None = Depends(require_api_key)
):
    payload = request.model_dump()
    if not approve_action("create_email_draft", payload):
        raise HTTPException(status_code=403, detail="Action rejected by user")

    try:
        result = create_email_draft(request.to, request.subject, request.body)
        return {"status": "success", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
