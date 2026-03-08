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


@app.post("/context", response_model=ContextResponse)
async def get_context(req: ContextRequest):
    """Fetch workspace context for a given query."""
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id="service_user",
        session_id=req.session_id,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=f"Find workspace context for: {req.query}")],
    )

    raw_text = ""
    async for event in runner.run(
        user_id="service_user",
        session_id=req.session_id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    raw_text += part.text

    try:
        result = json.loads(raw_text.strip().strip("```json").strip("```").strip())
        return ContextResponse(
            has_context=result.get("has_context", False),
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
            suggested_nudge_topic=result.get("suggested_nudge_topic", ""),
            raw_text=raw_text,
        )
    except (json.JSONDecodeError, AttributeError):
        return ContextResponse(
            has_context=False,
            raw_text=raw_text,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
