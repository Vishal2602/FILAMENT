# Filament — Claude Code Context

## What This Project Is
Filament is an ambient AI workspace co-pilot built for the **Build With AI NYC Hackathon 2026** (Live Agents category). It's a Chrome Extension + FastAPI backend that watches your screen, listens to your voice, and speaks proactive nudges by cross-referencing your Gmail and Google Drive.

## Team
- **Vishal Sunil Kumar** — original author, Google Cloud account (`vishals2602@gmail.com`)
- **Sanika** — co-presenter, running locally on MacBook (Apple Silicon)

## Architecture
```
Chrome Extension (content.js)
  ├── Screen capture: getDisplayMedia() → canvas → JPEG @ 1 frame/3s
  ├── Audio capture: getUserMedia() → AudioWorklet (worklet-processor.js) → PCM Int16 16kHz
  └── WebSocket → backend /ws

FastAPI Backend (main.py)
  ├── AGENT_MODE=local  → single Gemini Live session handles everything (CURRENT MODE on Cloud Run)
  └── AGENT_MODE=remote → 4 Cloud Run microservices (orchestrator routes to others via HTTP)

Gemini Live API (gemini-2.5-flash-native-audio-latest)
  └── Tool: fetch_workspace_context(query, source) → Gmail API + Drive API
```

## Key Files
- `extension/content.js` — orb UI, screen/mic capture, WebSocket, audio playback
- `extension/background.js` — OAuth, morning brief trigger, intent reader
- `extension/popup.js` / `popup.html` — settings panel, sign-in button
- `extension/manifest.json` — OAuth client ID, web_accessible_resources
- `extension/worklet-processor.js` — AudioWorklet PCM processor (separate file to bypass Gmail CSP)
- `backend/main.py` — WebSocket handler, Gemini Live session, tool calling
- `backend/tools.py` — `fetch_workspace_context` (Gmail + Drive)
- `backend/agents/live_agent.py` — system prompt for Gemini Live (local mode)
- `backend/services/screen_service.py` — screen analyst microservice (remote mode)
- `backend/services/workspace_service.py` — workspace context microservice (remote mode)
- `backend/services/nudge_service.py` — nudge composer microservice (remote mode)
- `backend/deploy.sh` — Cloud Run deployment script
- `backend/entrypoint.sh` — routes Docker container to correct service based on SERVICE_TARGET env var

## Deployed Services (Google Cloud Run — project: gcloud-hackathon-9er4rb4nr0k7a)
- **Orchestrator** (active, AGENT_MODE=local): `https://filament-orchestrator-sjs5thynia-uc.a.run.app`
- Screen Analyst: `https://filament-screen-analyst-sjs5thynia-uc.a.run.app`
- Workspace Agent: `https://filament-workspace-agent-sjs5thynia-uc.a.run.app`
- Nudge Composer: `https://filament-nudge-composer-sjs5thynia-uc.a.run.app`

**Note:** The orchestrator runs `AGENT_MODE=local` — it talks directly to Gemini Live API. The other 3 services are deployed but not used in the current flow.

## OAuth Setup
- OAuth Client ID: `76839905027-9mruei1o58bfots328vsp8a8k5l1suik.apps.googleusercontent.com`
- Google Cloud OAuth Project: `filament-490403`
- Google Cloud Deploy Project: `gcloud-hackathon-9er4rb4nr0k7a`
- Extension ID: `kaghjhkdpobhkkjnmjhcediamhbelool`
- Scopes: `gmail.readonly`, `drive.readonly`
- Test users: `sanikasawal2001@gmail.com`
- OAuth uses `launchWebAuthFlow` (implicit flow, `response_type=token`) — NOT `getAuthToken`

## Local Development Setup
```bash
# 1. Install Python 3.11
brew install python@3.11

# 2. Backend
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your GOOGLE_API_KEY

# 3. Run backend (local mode)
python main.py  # starts on http://localhost:8080

# 4. Load extension
# chrome://extensions/ → Developer mode → Load unpacked → select extension/
# Sign in via the popup before clicking the orb
```

## Environment Variables
- `GOOGLE_API_KEY` — Gemini API key from https://aistudio.google.com (required)
- `AGENT_MODE` — `local` (default, uses Gemini Live directly) or `remote` (routes to microservices)
- `GOOGLE_GENAI_USE_VERTEXAI` — set to `FALSE` to use API key (not Vertex AI)

## Deployment
```bash
# Authenticate (use Vishal's account)
gcloud auth login vishals2602@gmail.com
gcloud config set project gcloud-hackathon-9er4rb4nr0k7a

# Deploy all 4 services
cd backend
/opt/homebrew/bin/bash deploy.sh  # MUST use homebrew bash on macOS (bash 3.2 lacks associative arrays)

# Wire orchestrator to service URLs (only needed for remote mode)
export SCREEN_ANALYST_URL=https://filament-screen-analyst-sjs5thynia-uc.a.run.app
export WORKSPACE_AGENT_URL=https://filament-workspace-agent-sjs5thynia-uc.a.run.app
export NUDGE_COMPOSER_URL=https://filament-nudge-composer-sjs5thynia-uc.a.run.app
/opt/homebrew/bin/bash deploy.sh orchestrator

# Switch orchestrator to local mode (recommended — enables voice)
gcloud run services update filament-orchestrator \
  --project=gcloud-hackathon-9er4rb4nr0k7a \
  --region=us-central1 \
  --set-env-vars="AGENT_MODE=local,GOOGLE_API_KEY=<key>"
```

## Bugs Fixed (session 2026-03-16)
- `AlreadyExistsError` in screen/workspace/nudge services — `create_session` was called on every request; fixed with try/except get-or-create pattern
- OAuth token never reached workspace agent in remote mode — fixed token_holder threading through `_remote_ws_handler` → `_remote_pipeline` → `_call_workspace_agent`
- `workspace_service.py` — now calls `fetch_workspace_context` directly (bypasses broken ADK tool context in remote mode)
- AudioWorklet blob: URL blocked by Gmail CSP — moved to `worklet-processor.js` loaded via `chrome.runtime.getURL()`
- Extension context invalidated error in `chrome.storage` calls — wrapped in try/catch
- Gemini 2.5 thinking/reasoning leaking into text output — filtered with `getattr(part, 'thought', False)`
- Drive search only searched file content — now also searches by filename (`name contains`)
- `AGENT_MODE=remote` on orchestrator silently dropped all audio — switched to `AGENT_MODE=local`

## Known Issues & Decisions
- **Always use `/opt/homebrew/bin/bash deploy.sh`** — macOS ships with bash 3.2, deploy.sh uses bash 4+ associative arrays
- `PORT` is reserved in Cloud Run — do not set it in deploy.sh
- `AGENT_MODE=local` is required for voice interaction — remote mode does not forward audio to Gemini
- Drive API `fullText contains` only searches indexable content — now also uses `name contains` for filename search
- Gmail search operators work in the query: `in:sent`, `in:inbox`, `newer_than:1d`, `from:name`, `subject:keyword`
- Do NOT add hardcoded names/values (Sarah, NYC, tax rate) to system prompts — biases the model
- Extension loads `worklet-processor.js` via `chrome.runtime.getURL()` to bypass site CSP restrictions

## WebSocket URLs
- Local dev: `ws://localhost:8080/ws`
- Production: `wss://filament-orchestrator-sjs5thynia-uc.a.run.app/ws`
- Hardcoded as default in `extension/content.js` and `extension/popup.js`
- Users can override via the popup settings panel

## What Vishal Should Work On (UI)
- The reasoning/thinking text sometimes still leaks through — improve filtering or add better system prompt instructions
- Drive access needs testing — verify Drive API is enabled in project `filament-490403`
- Add a visual indicator when Filament is actively searching Gmail/Drive
- The panel UI could show which emails/files were found
- Demo video and submission writeup still needed

## Hackathon Submission Checklist
- [x] Public GitHub repo: https://github.com/Vishal2602/FILAMENT
- [x] Backend deployed on Google Cloud Run
- [x] Uses Gemini Live API (gemini-2.5-flash-native-audio-latest)
- [x] Uses Google GenAI SDK + ADK
- [x] Uses Gmail API + Drive API (Google Cloud services)
- [x] Automated deployment scripts (deploy.sh)
- [x] Voice interaction working (AGENT_MODE=local on orchestrator)
- [x] Gmail access working (received emails confirmed)
- [ ] Drive access needs verification
- [ ] Architecture diagram
- [ ] Demo video (<4 min)
- [ ] Text description / submission writeup
