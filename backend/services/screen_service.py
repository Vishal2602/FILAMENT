"""Standalone FastAPI service for the Screen Analyst agent.

Deploy as its own Cloud Run instance for independent scaling.
Accepts screen frames via POST, returns structured analysis.

Usage:
  uvicorn services.screen_service:app --port 8001
"""

import asyncio
import base64
import json
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.screen_analyst import screen_analyst_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Filament — Screen Analyst Service")

session_service = InMemorySessionService()
APP_NAME = "filament_screen"

runner = Runner(
    agent=screen_analyst_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


class FrameRequest(BaseModel):
    frame_b64: str  # base64-encoded JPEG
    session_id: str = "default"


class AnalysisResponse(BaseModel):
    pattern: str
    confidence: float
    details: str
    context_query: str
    app: str
    idle_seconds: float | None = None
    raw_text: str = ""


@app.get("/health")
async def health():
    return {"status": "screen_analyst running", "agent": "screen_analyst"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_frame(req: FrameRequest):
    """Analyze a single screen frame and return structured observations."""
    try:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id="service_user",
            session_id=req.session_id,
        )
    except Exception:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id="service_user",
            session_id=req.session_id,
        )

    frame_bytes = base64.b64decode(req.frame_b64)

    content = types.Content(
        role="user",
        parts=[
            types.Part(
                inline_data=types.Blob(
                    mime_type="image/jpeg",
                    data=frame_bytes,
                )
            ),
            types.Part(text="Analyze this screen capture."),
        ],
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

    # Parse the JSON from the agent's response
    try:
        result = json.loads(raw_text.strip().strip("```json").strip("```").strip())
        return AnalysisResponse(
            pattern=result.get("pattern", "none"),
            confidence=result.get("confidence", 0.0),
            details=result.get("details", ""),
            context_query=result.get("context_query", ""),
            app=result.get("app", "other"),
            idle_seconds=result.get("idle_seconds"),
            raw_text=raw_text,
        )
    except (json.JSONDecodeError, AttributeError):
        return AnalysisResponse(
            pattern="none",
            confidence=0.0,
            details="Failed to parse agent response",
            context_query="",
            app="other",
            raw_text=raw_text,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
