# TextShield Desktop

A native Windows desktop shell for the existing TextShield FastAPI backend.

It provides:

- A floating, always-on-top launcher.
- A compact frameless overlay with text/SMS/email analysis and navigation.
- A full window with Analyze, History, Knowledge Base, and Threat Intelligence pages.
- A tray icon with show/hide, explicit clipboard actions, launcher, always-on-top, dashboard, settings, reconnect, start-with-Windows, and quit actions.
- A configurable global hotkey (default `Ctrl+Alt+Shift+T`) that opens or hides the overlay and focuses the input. It never submits automatically.
- Explicit clipboard review before analysis. TextShield reads the clipboard only after **Analyze Clipboard** is chosen (or after **Copy Selected Text** performs an explicit copy), and sends it only after **Analyze** is confirmed in the review dialog.
- Per-user start-with-Windows support through `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- Backend health polling and clear offline/HTTP/validation errors.
- Analysis through the real `POST /api/analyze` endpoint.
- Saved overlay/launcher positions and display-aware placement.

It intentionally does **not** include clipboard monitoring, keylogging, OCR,
screen capture, browser extensions, or background inspection of other
applications. Clipboard and selected-text access is explicit, one-shot, and
never logged.

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
routes, clipboard monitoring, keylogging, OCR, screen capture, and browser
extensions. Explicit clipboard review and explicit selected-text copy are
supported.

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

- Press the global hotkey (default `Ctrl+Alt+Shift+T`) to open or hide the
  overlay and focus the analysis input. Change it in Settings; registration
  conflicts are reported there.
- Click the floating launcher to show the overlay.
- Drag the launcher or overlay title bar to reposition it.
- The overlay hides when it loses focus by default. Change this in Settings.
- The overlay title-bar **☰** button opens navigation: Analyze, History,
  Knowledge Base, Threat Intelligence, Intelligence, Research, Settings, and
  Open Full Dashboard.
- The tray icon opens the overlay on left click; right click shows the menu.
- Closing the overlay or main window hides them; use **Quit** in the tray menu
  or the launcher context menu to exit.
- **Analyze Clipboard** reads the current clipboard text once, shows a preview,
  and sends it only after you choose **Analyze**. **Copy Selected Text** restores
  the previous application, sends an explicit Ctrl+C, and then shows the same
  review dialog. **Clear Clipboard** asks for confirmation before clearing.
- **Start with Windows** creates or removes a per-user startup entry. Startup
  launches the tray app with `--startup` and keeps the launcher hidden when a
  tray icon is available.
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
- When the backend is offline, the tray status and analysis errors say so;
  **Reconnect Backend** triggers an immediate health check and the normal
  five-second poll recovers automatically.

## Tests

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest desktop\tests -q -o addopts=""

# Native Windows run, including RegisterHotKey/WM_HOTKEY and startup registry:
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m pytest desktop\tests -q -o addopts=""
```

The desktop tests include a local fake HTTP server; they do not require the
real backend. Global-hotkey registration needs the native Windows platform, so
the offscreen suite skips that one test. The real-backend smoke test does:

```powershell
.\.venv\Scripts\python.exe desktop\run_desktop.py --smoke-test --smoke-report desktop\build\smoke-report.json
```

The smoke test checks launcher/overlay visibility, hide/reopen, always-on-top,
the overlay menu, all main-window sections, history/KB/threat-intel loading, an
IOC check, backend health, tray actions, clipboard availability, startup
availability, and one real `/api/analyze` request. With the native Windows
platform it also checks global-hotkey registration and the hotkey-to-overlay
path. Intelligence and Research are checked as present-but-unavailable.

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
- `textshield_desktop.ui.settings_dialog` — backend URL, hotkey, startup, and
  window preferences.
- `textshield_desktop.ui.clipboard_dialog` — explicit clipboard/selection review
  before sending text.
- `textshield_desktop.native.windows` — foreground-window, explicit Ctrl+C, and
  clipboard sequence helpers.
- `textshield_desktop.native.hotkey` — `RegisterHotKey` and `WM_HOTKEY` filter.
- `textshield_desktop.native.clipboard` — one-shot clipboard read/clear and
  selected-text capture.
- `textshield_desktop.native.startup` — per-user Windows startup registry.

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
- Clipboard monitoring, keylogging, OCR, screen capture, and browser extensions
  are out of scope. Only explicit clipboard/selection actions are supported.
- **Copy Selected Text** is best-effort: the other application must accept
  Ctrl+C and expose the selection as text. Elevated/UAC windows, games, and
  some custom controls may refuse focus or copy.
- The global hotkey can conflict with another application. TextShield reports
  the conflict and keeps the previous shortcut; choose another in Settings.
- Start with Windows is per-user. The registry value is not created until the
  option is enabled, and the app does not manage backend startup.
- Offscreen test runs cannot register native Windows hotkeys; use the native
  test/smoke run for that check.

## Manual interaction matrix

Run these on a real Windows desktop:

- With a text editor focused, press the hotkey twice: the overlay opens, focuses
  the input, and hides again without submitting.
- Copy text in another app, choose **Analyze Clipboard**, verify the preview,
  and confirm. The result appears in the overlay.
- Select text in Notepad or a browser, press the hotkey, choose **Copy Selected
  Text**, review, and confirm. Try an app that refuses Ctrl+C and verify the
  explanatory error.
- Clear the clipboard from the tray and from the overlay link; verify the
  confirmation and that no content is logged.
- Toggle **Start with Windows**, sign out/in (or inspect the Run key), and
  verify the tray app starts with the launcher hidden.
- Stop the backend: tray/overlay show offline and analysis explains the failure.
  Restart it and use **Reconnect Backend**; verify recovery.
- Move the overlay/launcher across monitors and change Windows scaling; verify
  saved positions remain reachable.
