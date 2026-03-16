"""Standalone FastAPI service for the Nudge Composer agent.

Deploy as its own Cloud Run instance for independent scaling.
Accepts screen analysis + workspace context, returns the spoken nudge.
This service uses the native audio model for voice output.

Usage:
  uvicorn services.nudge_service:app --port 8003
"""

import asyncio
import base64
import json
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.agents.live_request_queue import LiveRequestQueue, LiveRequest
from google.adk.agents.run_config import RunConfig
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.nudge_composer import nudge_composer_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Filament — Nudge Composer Service")

session_service = InMemorySessionService()
APP_NAME = "filament_nudge"

runner = Runner(
    agent=nudge_composer_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


class NudgeRequest(BaseModel):
    screen_analysis: dict
    workspace_context: dict
    session_id: str = "default"


class NudgeResponse(BaseModel):
    nudge_text: str
    should_speak: bool


@app.get("/health")
async def health():
    return {"status": "nudge_composer running", "agent": "nudge_composer"}


@app.post("/compose", response_model=NudgeResponse)
async def compose_nudge(req: NudgeRequest):
    """Compose a text nudge from screen analysis and workspace context."""
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

    prompt = (
        f"Screen Analysis:\n{json.dumps(req.screen_analysis, indent=2)}\n\n"
        f"Workspace Context:\n{json.dumps(req.workspace_context, indent=2)}\n\n"
        "Compose the spoken nudge now."
    )
    content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
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

    nudge = raw_text.strip()
    should_speak = nudge and nudge != "[SILENCE]"

    return NudgeResponse(nudge_text=nudge, should_speak=should_speak)


@app.websocket("/ws/audio")
async def nudge_audio_ws(websocket: WebSocket):
    """WebSocket endpoint for streaming audio nudges.

    The orchestrator connects here to get audio output from the nudge composer.
    Send a JSON message with screen_analysis and workspace_context,
    receive PCM audio bytes back.
    """
    await websocket.accept()
    logger.info("Nudge audio WebSocket connected")

    session_id = f"nudge_session_{id(websocket)}"
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id="service_user",
        session_id=session_id,
    )

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            live_queue = LiveRequestQueue()

            prompt = (
                f"Screen Analysis:\n{json.dumps(data.get('screen_analysis', {}), indent=2)}\n\n"
                f"Workspace Context:\n{json.dumps(data.get('workspace_context', {}), indent=2)}\n\n"
                "Compose and speak the nudge now."
            )
            text_blob = types.Blob(
                mime_type="text/plain",
                data=prompt.encode(),
            )
            live_queue.send(LiveRequest(blob=text_blob))
            live_queue.close()

            run_config = RunConfig(
                response_modalities=[types.Modality.AUDIO],
            )
            async for event in runner.run_live(
                session=session,
                live_request_queue=live_queue,
                run_config=run_config,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                            await websocket.send_bytes(part.inline_data.data)
                        elif part.text:
                            await websocket.send_text(json.dumps({
                                "type": "text",
                                "content": part.text,
                            }))

    except WebSocketDisconnect:
        logger.info("Nudge audio client disconnected")
    except Exception as e:
        logger.error(f"Nudge audio error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8003)))
