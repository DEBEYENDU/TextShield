# TextShield Desktop

A native Windows desktop shell for the existing TextShield FastAPI backend.

It provides:

- A floating, always-on-top launcher.
- A compact frameless overlay with text/SMS/email analysis and navigation.
- A full window with Analyze, History, Knowledge Base, and Threat Intelligence pages.
- A tray icon with show/hide, launcher, always-on-top, dashboard, settings, and quit actions.
- Backend health polling and clear offline/HTTP/validation errors.
- Analysis through the real `POST /api/analyze` endpoint.
- Saved overlay/launcher positions and display-aware placement.

It intentionally does **not** include clipboard monitoring, OCR, screen capture,
browser extensions, or background inspection of other applications. The user
pastes or types text into the overlay or main window.

## Connected and unavailable features

| Area | Status | Backend |
| --- | --- | --- |
| Analyze (text, SMS, email) | Connected | `POST /api/analyze` |
| History | Connected, read-only | `GET /api/history` |
| Knowledge Base | Connected; status and confirmed rebuild | `GET /api/knowledge-base`, `POST /api/knowledge-base/rebuild` |
| Threat Intelligence | Connected; providers, status, IOC checks | `GET /api/threat-intel/providers`, `GET /api/threat-intel/status`, `POST /api/threat-intel/check` |
| Intelligence | Unavailable | Router is not registered in `app/main.py`; no candidate generator is wired |
| Research | Unavailable | Router is not registered in `app/main.py`; requests are an in-memory stub with no execution worker |

Intelligence and Research remain visible in the navigation so the gap is clear.
They show an explanation page and never substitute mock data.

Unavailable in this desktop phase: authentication, analytics/v2/graph/semantic
routes, clipboard monitoring, OCR, screen capture, and browser extensions.

## Requirements

- Windows 10 or later.
- Python 3.11+.
- The TextShield backend dependencies from the repository root.
- Desktop dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r desktop\requirements-desktop.txt
```

Development/test/build extras:

```powershell
.\.venv\Scripts\python.exe -m pip install -r desktop\requirements-dev.txt
```

## Run

Start the existing backend in one terminal:

```powershell
.\.venv\Scripts\python.exe run.py
```

Start the desktop shell in another terminal:

```powershell
.\.venv\Scripts\python.exe desktop\run_desktop.py
```

Use a different backend URL:

```powershell
.\.venv\Scripts\python.exe desktop\run_desktop.py --backend-url http://127.0.0.1:9000
```

The URL can also be set in **Settings** or with `TEXTSHIELD_BACKEND_URL`.
`QSettings` stores the value under `TextShield/TextShieldDesktop`.

## Behavior

- Click the floating launcher to show the overlay.
- Drag the launcher or overlay title bar to reposition it.
- The overlay hides when it loses focus by default. Change this in Settings.
- The overlay title-bar **☰** button opens navigation: Analyze, History,
  Knowledge Base, Threat Intelligence, Intelligence, Research, Settings, and
  Open Full Dashboard.
- The tray icon opens the overlay on left click; right click shows the menu.
- Closing the overlay or main window hides them; use **Quit** in the tray menu
  or the launcher context menu to exit.
- **Analyze** supports Text, SMS, and Email input:
  - Text/SMS sends `{"input_type": "...", "message": "..."}`.
  - Email sends `{"input_type": "email", "email_raw": "..."}`.
  - Results show classification, confidence, risk, explanation, recommendation,
    indicators, URLs, risk factors, and RAG evidence.
- `Ctrl+Enter` / `Ctrl+Return` submits the analysis.
- **History** is read-only with input-type, classification, and risk filters plus
  25-row pagination.
- **Knowledge Base** shows collection status and asks for confirmation before a
  rebuild. Rebuilds use the existing backend/vector store; no second store is
  created.
- **Threat Intelligence** shows configured providers, cache/reputation status,
  and IOC verdicts. The desktop app never visits the checked URL itself.
- **Open Full Dashboard** launches the existing web UI at the configured
  backend URL.

## Tests

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest desktop\tests -q
```

The desktop tests include a local fake HTTP server; they do not require the
real backend. The real-backend smoke test does:

```powershell
.\.venv\Scripts\python.exe desktop\run_desktop.py --smoke-test --smoke-report desktop\build\smoke-report.json
```

The smoke test checks launcher/overlay visibility, hide/reopen, always-on-top,
the 8-item overlay menu, all main-window sections, history/KB/threat-intel
loading, an IOC check, backend health, and one real `/api/analyze` request.
Intelligence and Research are checked as present-but-unavailable.

## Build

```powershell
powershell -ExecutionPolicy Bypass -File desktop\packaging\build.ps1
```

Output:

```text
desktop\dist\TextShieldDesktop\TextShieldDesktop.exe
```

The build is a one-directory PyInstaller bundle. The backend is not bundled;
start `run.py` separately or point the desktop app at a running backend.

## Icon

The source is `desktop/src/textshield_desktop/resources/icons/textshield.svg`.
Regenerate the PNG/ICO files with:

```powershell
.\.venv\Scripts\python.exe desktop\tools\make_icon.py
```

## Architecture

- `textshield_desktop.app` — application bootstrap, tray/launcher/overlay/main
  window wiring, health timer, settings application, shutdown, smoke test.
- `textshield_desktop.backend.client` — async QtNetwork client for the existing
  health, analysis, history, KB, and threat-intel endpoints; no backend imports.
- `textshield_desktop.ui.overlay` — frameless always-on-top overlay and menu.
- `textshield_desktop.ui.launcher` — floating draggable launcher.
- `textshield_desktop.ui.main_window` — full window with sidebar navigation.
- `textshield_desktop.ui.pages.history_page` — read-only history browser.
- `textshield_desktop.ui.pages.knowledge_page` — KB status and rebuild.
- `textshield_desktop.ui.pages.threat_intel_page` — providers, status, IOC checks.
- `textshield_desktop.ui.pages.unavailable_page` — transparent placeholders for
  Intelligence and Research.
- `textshield_desktop.ui.result_view` — analysis response renderer.
- `textshield_desktop.ui.settings_dialog` — backend URL and window preferences.

## Known limitations

- Backend lifecycle is not managed by the desktop app. Start/stop `run.py`
  yourself; the app reports offline status when it is unavailable.
- Authentication is not wired in the current backend, so the desktop app does
  not send API keys. Keep the backend bound to loopback.
- Intelligence and Research are unavailable because their routers are not
  registered and their execution paths are incomplete. The app does not fake
  these features.
- The overlay is a compact summary. Full evidence is shown in the main window
  and the existing web dashboard.
- The launcher is a floating window, not a Windows shell taskbar toolbar.
- Clipboard monitoring, OCR, screen capture, and browser extensions are out of
  scope.
