"""Standalone FastAPI service for the Workspace Context agent.

Deploy as its own Cloud Run instance for independent scaling.
Accepts a search query, returns structured Gmail + Drive context.

Usage:
  uvicorn services.workspace_service:app --port 8002
"""

import asyncio
import json
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.workspace_agent import workspace_agent
from tools import fetch_workspace_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Filament — Workspace Context Service")

session_service = InMemorySessionService()
APP_NAME = "filament_workspace"

runner = Runner(
    agent=workspace_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


class ContextRequest(BaseModel):
    query: str
    session_id: str = "default"
    oauth_token: str = ""


class EmailSummary(BaseModel):
    sender: str = ""
    subject: str = ""
    snippet: str = ""
    date: str = ""


class FileSummary(BaseModel):
    name: str = ""
    last_edited: str = ""
    link: str = ""


class ContextResponse(BaseModel):
    has_context: bool
    emails: list[EmailSummary] = []
    files: list[FileSummary] = []
    key_facts: list[str] = []
    suggested_nudge_topic: str = ""
    raw_text: str = ""


@app.get("/health")
async def health():
    return {"status": "workspace_context running", "agent": "workspace_context"}


class _ToolCtx:
    def __init__(self, token):
        self.state = {"oauth_token": token}


@app.post("/context", response_model=ContextResponse)
async def get_context(req: ContextRequest):
    """Fetch workspace context for a given query using the user's OAuth token."""
    if not req.oauth_token:
        logger.warning("No oauth_token in request — cannot fetch Gmail/Drive")
        return ContextResponse(has_context=False)

    result = fetch_workspace_context(
        query=req.query,
        source="both",
        tool_context=_ToolCtx(req.oauth_token),
    )

    has_context = result.get("source") == "live" and (result.get("emails") or result.get("files"))
    return ContextResponse(
        has_context=bool(has_context),
        emails=[EmailSummary(
            sender=e.get("from", ""),
            subject=e.get("subject", ""),
            snippet=e.get("snippet", ""),
            date=e.get("date", ""),
        ) for e in result.get("emails", [])],
        files=[FileSummary(
            name=f.get("name", ""),
            last_edited=f.get("last_edited", ""),
            link=f.get("link", ""),
        ) for f in result.get("files", [])],
        key_facts=result.get("key_facts", []),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
