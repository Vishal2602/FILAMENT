```
   ███████╗██╗██╗      █████╗ ███╗   ███╗███████╗███╗   ██╗████████╗
   ██╔════╝██║██║     ██╔══██╗████╗ ████║██╔════╝████╗  ██║╚══██╔══╝
   █████╗  ██║██║     ███████║██╔████╔██║█████╗  ██╔██╗ ██║   ██║
   ██╔══╝  ██║██║     ██╔══██║██║╚██╔╝██║██╔══╝  ██║╚██╗██║   ██║
   ██║     ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗██║ ╚████║   ██║
   ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝

        ┌─────────────────────────────────────────────────┐
        │   Ambient AI Workspace Co-Pilot                 │
        │   No text box. No prompt. No button.            │
        │   Just presence.                                │
        └─────────────────────────────────────────────────┘

                    ╭──────╮
                   ╱  ◉  ◉  ╲       ← Filament sees your screen
                  │    ▽     │       ← listens to your voice
                  │  ╰───╯   │       ← speaks when it matters
                   ╲________╱
                    │ ││ ││ │
                    ╰─╯╰─╯╰─╯
```

# Filament

**An ambient AI workspace co-pilot that watches your screen, listens to your voice, cross-references your Google Workspace data, and speaks at the right moment.**

Built for the **Build With AI NYC Hackathon 2026** — Live Agent Category.

---

## How It Works

```
  ┌──────────────────┐       WebSocket        ┌──────────────────────┐
  │  Chrome Extension │◄─────────────────────►│   FastAPI Backend     │
  │                    │  frames + audio (in)  │                      │
  │  Screen Capture    │  audio + text  (out)  │  Gemini Live API     │
  │  Mic Capture       │                       │  (bidiGenerateContent)│
  │  Audio Playback    │                       │                      │
  │  Floating Orb UI   │                       │  Tool: Gmail + Drive │
  └──────────────────┘                        └──────────────────────┘
         │                                              │
         │  getDisplayMedia()                           │  fetch_workspace_context()
         │  getUserMedia()                              │
         ▼                                              ▼
    User's Screen                               Google Workspace
    + Microphone                                Gmail API + Drive API
```

1. **You click the floating orb** on any webpage
2. Filament starts capturing your screen (1 frame/3s) and microphone
3. Frames and audio stream to the backend over WebSocket
4. The backend pipes everything into the **Gemini Live API** (`gemini-2.5-flash-native-audio-latest`)
5. When the model spots something actionable, it calls `fetch_workspace_context` to search your **Gmail and Google Drive**
6. It **speaks a short nudge** back to you — audio played directly in your browser
7. You can also **talk to it** naturally and it responds with voice

---

## Demo Scenarios

### Scenario 1: The Incomplete Invoice (Main Demo)
```
User opens Google Sheet → invoice with empty Tax Rate cell
        ↓  (Filament watches for ~8 seconds)
Filament calls fetch_workspace_context("invoice tax rate NYC")
        ↓  (finds boss's email)
Filament speaks: "The tax rate on row 14 looks empty.
                  Your boss Sarah mentioned 8.5% for NYC clients on Tuesday."
```

### Scenario 2: Navigation Detection
```
User switches from Google Sheets → Gmail
        ↓  (background.js detects navigation pattern)
Filament speaks: "You're probably here to send the invoice —
                  I can see the file was last edited 47 minutes ago."
```

### Scenario 3: Morning Brief
```
User opens new tab before 11am
        ↓  (morning_brief trigger)
Filament speaks: "Good morning! You have 3 unread emails,
                  and the Q1 report was shared with you yesterday."
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Extension | Chrome Extension Manifest V3, Vanilla JS |
| Screen Capture | `getDisplayMedia()` → canvas → JPEG @ 1fps |
| Audio Capture | `getUserMedia()` → AudioWorklet → PCM Int16 16kHz |
| Transport | WebSocket (bidirectional, persistent) |
| Backend | FastAPI (Python 3.11) on Google Cloud Run |
| AI Model | `gemini-2.5-flash-native-audio-latest` via Gemini Live API |
| Workspace Data | Gmail API + Drive API via OAuth 2.0 |
| Voice Output | Web Audio API, PCM 24kHz sequential playback |
| Deployment | Google Cloud Run, us-central1 |

---

## Project Structure

```
filament/
├── README.md                    ← you are here
├── CLAUDE.md                    ← AI assistant context
├── extension/                   ← Chrome Extension (Manifest V3)
│   ├── manifest.json            ← permissions, OAuth scopes
│   ├── content.js               ← orb UI, screen/mic capture, audio playback
│   ├── background.js            ← morning brief + intent reader triggers
│   ├── popup.html / popup.js    ← settings (backend URL config)
│   └── orb.css                  ← floating orb + panel styles
├── backend/                     ← FastAPI Python backend
│   ├── main.py                  ← WebSocket handler, Gemini Live session
│   ├── tools.py                 ← fetch_workspace_context (Gmail + Drive)
│   ├── agents/
│   │   └── live_agent.py        ← system prompt for the Gemini model
│   ├── services/                ← microservice endpoints (remote mode)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml       ← local multi-service dev
│   ├── cloudbuild.yaml          ← Cloud Build CI/CD
│   ├── deploy.sh                ← Cloud Run deployment
│   ├── setup-iam.sh             ← service-to-service auth
│   └── entrypoint.sh            ← routes to correct service
└── .gitignore
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Google API Key (from [AI Studio](https://aistudio.google.com))
- Chrome browser
- Google Cloud project with Gmail & Drive APIs enabled (for live workspace data)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
GOOGLE_API_KEY=your_gemini_api_key
AGENT_MODE=local
EOF

# Run
python main.py
```

The backend starts on `http://localhost:8080`.

### 2. Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked** → select the `extension/` folder
4. Navigate to any webpage
5. Click the **Filament orb** (bottom right corner)
6. Grant screen sharing and microphone permissions
7. Start talking or just watch — Filament will speak when it sees something useful

### 3. OAuth (Optional — for live Gmail/Drive)

To access real workspace data instead of empty results:

1. Set up OAuth 2.0 credentials in Google Cloud Console
2. Add the OAuth client ID to `manifest.json` under `oauth2.client_id`
3. The extension sends the OAuth token to the backend on WebSocket connect
4. The backend uses it to query Gmail and Drive on your behalf

---

## Architecture Modes

Filament supports two execution modes:

### Local Mode (Default)
Single process — the backend opens one Gemini Live session that handles everything:
screen analysis, workspace lookup, and spoken nudge generation.

```
Extension ←→ WebSocket ←→ main.py ←→ Gemini Live API
                                          ↕
                                   fetch_workspace_context()
```

### Remote Mode (Cloud Run)
Microservices — each agent runs as a separate Cloud Run instance:

```
Extension ←→ WebSocket ←→ Orchestrator
                              ├──→ Screen Analyst   (analyzes frames)
                              ├──→ Workspace Agent  (Gmail + Drive lookup)
                              └──→ Nudge Composer   (generates spoken output)
```

Set `AGENT_MODE=remote` and configure service URLs in `.env`.

---

## Key Design Decisions

- **Voice-first**: The primary output is always spoken audio, not text. Text appears in the panel as a secondary transcript.
- **Proactive, not reactive**: Filament doesn't wait for you to ask. It watches your screen and speaks when it has something worth saying.
- **No mock data**: All workspace data comes from real Gmail and Drive API calls. If OAuth isn't configured, the tool returns empty results honestly.
- **Single Live session**: Uses the Gemini Live API's `bidiGenerateContent` for real-time bidirectional streaming — frames and audio in, spoken audio out.
- **End-of-turn signaling**: Every ~9 seconds, the backend sends an `end_of_turn` signal to the Gemini session, prompting the model to analyze accumulated frames and respond.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini API key from AI Studio |
| `AGENT_MODE` | No | `local` (default) or `remote` |
| `PORT` | No | Backend port (default: 8080) |
| `SCREEN_ANALYST_URL` | Remote only | URL for screen analyst service |
| `WORKSPACE_AGENT_URL` | Remote only | URL for workspace agent service |
| `NUDGE_COMPOSER_URL` | Remote only | URL for nudge composer service |

---

## Deployment (Cloud Run)

```bash
# Build and deploy all services
chmod +x backend/deploy.sh
./backend/deploy.sh

# Or use Cloud Build
gcloud builds submit --config backend/cloudbuild.yaml
```

---

## Team

| Name | Role | Contact |
|---|---|---|
| **Vishal Sunil Kumar** | Founding Engineer | vishals2602@gmail.com |
| **Sanika** | Co-presenter | |

---

## License

Built for the Build With AI NYC Hackathon 2026. All rights reserved.

---

```
        ╔═══════════════════════════════════════════════╗
        ║                                               ║
        ║   "The best interface is no interface."        ║
        ║                                               ║
        ║   Filament doesn't wait for you to ask.       ║
        ║   It watches. It listens. It speaks            ║
        ║   when it matters.                             ║
        ║                                               ║
        ╚═══════════════════════════════════════════════╝
```
