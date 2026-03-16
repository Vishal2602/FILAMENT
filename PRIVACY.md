# Privacy Policy

**Last updated: March 16, 2026**

Filament ("we", "our", or "the extension") is an ambient AI workspace co-pilot that operates as a Chrome Extension. This Privacy Policy explains what data Filament accesses, how it is used, and how it is protected.

---

## 1. Data We Access

To provide its features, Filament accesses the following data during an active session:

- **Screen content** — captured as JPEG frames (1 per 3 seconds) via `getDisplayMedia()` while screen sharing is active. Frames are streamed to the Filament backend for real-time analysis and are never stored.
- **Microphone audio** — captured as PCM audio via `getUserMedia()` while a session is active. Audio is streamed to the Filament backend and is never stored or recorded.
- **Gmail data** — with your explicit OAuth consent, Filament may search your Gmail inbox to surface relevant context. Access is read-only (`gmail.readonly` scope). Filament does not read, store, or transmit your emails beyond what is needed to answer a specific query.
- **Google Drive data** — with your explicit OAuth consent, Filament may search your Drive files to surface relevant context. Access is read-only (`drive.readonly` scope). File contents are not stored.

---

## 2. Data We Do NOT Collect or Store

- We do not store screen frames, audio recordings, email content, or file content on any server.
- We do not build user profiles or retain any personal data between sessions.
- We do not sell, share, or transfer any data to third parties.
- OAuth tokens are held only in your browser's local storage for the duration of your session and are used solely to make authenticated API calls on your behalf.

---

## 3. How Data Is Used

All data accessed by Filament is used exclusively to provide real-time, in-session AI assistance:

- Screen frames and audio are sent to the Gemini Live API (Google) for multimodal analysis.
- Gmail and Drive queries are made only when the AI determines relevant workspace context is needed to answer a question or surface a nudge.
- No data is retained after your session ends.

---

## 4. Third-Party Services

| Service | Purpose | Privacy Policy |
|---|---|---|
| Google Gemini Live API | Real-time multimodal AI processing | [Google Privacy Policy](https://policies.google.com/privacy) |
| Gmail API | Read-only email search | [Google Privacy Policy](https://policies.google.com/privacy) |
| Google Drive API | Read-only file search | [Google Privacy Policy](https://policies.google.com/privacy) |
| Google Cloud Run | Hosts the Filament backend | [Google Privacy Policy](https://policies.google.com/privacy) |

---

## 5. Permissions

Filament requests the following Chrome permissions:

| Permission | Reason |
|---|---|
| `storage` | Save your backend URL preference and OAuth token locally |
| `identity` | Initiate the Google OAuth flow for Gmail and Drive access |
| `tabs` | Detect tab navigation for the intent reader feature |
| `scripting`, `activeTab` | Inject the Filament UI on the current page |

Screen and microphone access are requested only when you explicitly click to start a session.

---

## 6. Data Security

All communication between the Chrome Extension and the Filament backend is encrypted using WSS (WebSocket Secure) and HTTPS. The backend runs on Google Cloud Run in us-central1.

---

## 7. Children's Privacy

Filament is not directed at children under 13. We do not knowingly collect data from children.

---

## 8. Changes to This Policy

We may update this Privacy Policy from time to time. Changes will be reflected in this file with an updated date.

---

## 9. Contact

Questions about this Privacy Policy? Contact us at [vishals2602@gmail.com](mailto:vishals2602@gmail.com).

---

Filament is open source — view the full source code at [github.com/Vishal2602/FILAMENT](https://github.com/Vishal2602/FILAMENT).
