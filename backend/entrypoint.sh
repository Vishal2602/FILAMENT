#!/bin/bash
set -e

PORT="${PORT:-8080}"

case "${SERVICE_TARGET}" in
  screen)
    echo "Starting Screen Analyst service on port ${PORT}"
    exec python -m uvicorn services.screen_service:app --host 0.0.0.0 --port "${PORT}"
    ;;
  workspace)
    echo "Starting Workspace Context service on port ${PORT}"
    exec python -m uvicorn services.workspace_service:app --host 0.0.0.0 --port "${PORT}"
    ;;
  nudge)
    echo "Starting Nudge Composer service on port ${PORT}"
    exec python -m uvicorn services.nudge_service:app --host 0.0.0.0 --port "${PORT}"
    ;;
  *)
    echo "Starting Orchestrator service on port ${PORT}"
    exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT}"
    ;;
esac
