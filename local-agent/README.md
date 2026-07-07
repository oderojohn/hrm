# Emboita Sync Agent

A standalone desktop app that runs on a PC next to a ZKTeco biometric device.
It polls the device on an interval, stores every punch in a local SQLite
database, and pushes only the punches it hasn't pushed yet to the Emboita
Hotel HRM cloud — so the cloud stays up to date even when the device itself
has no direct route to the internet.

## Getting an API key

Before configuring the agent, a Super Admin must create a Sync Agent entry
in the cloud web app under **System Settings → Sync Agents → New Agent**.
The API key is shown exactly once at creation — copy it into this app's
Settings screen (see below) before closing that dialog.

## Running from source (development)

```
cd local-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m agent.main
```

On first launch the app has no configuration. Open **Settings**, fill in:
- **Cloud URL** — e.g. `http://localhost:8000` for local dev, or your
  production HRM URL.
- **API Key** — the key copied from the cloud's Sync Agents page.
- **Sync Interval** — how often (in minutes) to check the device for new
  punches.
- **ZK Devices** — add one row per physical device this installation should
  poll (name, IP address, port — default port is 4370).

Click **Test Connection** to confirm the API key is valid before saving.
Once saved, the agent starts polling automatically in the background; use
**Sync Now** at any time to trigger an immediate out-of-cycle sync.

Local data (config + SQLite punch history) lives under
`%APPDATA%\EmboitaSyncAgent\`.

## Building the distributable .exe

```
cd local-agent
pip install -r requirements.txt
pyinstaller --onefile --windowed --name EmboitaSyncAgent agent/main.py
```

The resulting executable is written to `dist/EmboitaSyncAgent.exe` — copy
that single file to the target PC and double-click to run. No Python
installation is required on that machine.
