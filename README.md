# GMapProspect

Local Google Maps scraping and lead management tool.

The project runs **on the user's machine**.

- scrape Google Maps leads with Playwright
- store and qualify prospects locally
- work leads from a dashboard, swipe flow, or call flow
- track call history, notes, and durations

## Table of contents

- [What the project does](#what-the-project-does)
- [Stack](#stack)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Data flow](#data-flow)
- [LLM integration](#llm-integration)
- [Generated data](#generated-data)
- [Recommended workflow](#recommended-workflow)
- [Call history](#call-history)
- [Important](#important)
- [Useful commands](#useful-commands)
- [Current limitations](#current-limitations)
- [License](#license)

## What the project does

- scrapes Google Maps leads from a search query
- turns scraped results into prospect records
- imports these records into a local SQLite CRM-like workflow
- lets you qualify, contact, and review leads locally
- exposes a local web app through:
  - `/`: main dashboard
  - `/swipe`: quick lead triage
  - `/prospection`: focused call mode
  - `/history`: call history

## Stack

- Python
- Playwright + Chromium
- SQLite
- HTML / CSS / JS vanilla
- local HTTP server via `server.py`
- FastMCP for local agent tooling

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/HamzaDams/GMapProspect.git
cd GMapProspect
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Chromium for Playwright

```bash
python3 -m playwright install chromium
```

## Quick start

### Recommended option: run the local app

```bash
python3 server.py
```

Then open:

```text
http://localhost:8000
```

From this interface, you can:

- start a scrape
- browse prospects
- change their status
- take notes
- use swipe mode
- use call mode
- view call history

### CLI option: run only the scraper

```bash
python3 main.py -s "hotels in Paris" -t 20
```

Arguments:

- `-s`, `--search`: Google Maps query
- `-t`, `--total`: number of leads to fetch

## Data flow

The current flow is:

1. `main.py` scrapes Google Maps results
2. the scraper writes a compatibility CSV file to `results.csv`
3. the scraper also appends structured prospect records to `prospects.json`
4. `server.py` imports `prospects.json` into `prospects.db`
5. the dashboard and API work from `prospects.db`
6. the `Export CSV` button exports from the database, not from `results.csv`

So yes: `results.csv` still exists, but it is now a secondary artifact from the raw scraper, not the main data source of the app.

## LLM integration

This repository now includes a local agent layer so tools like Claude Code or Codex can operate the app through structured tools instead of raw shell commands.

### Included pieces

- `server.py`: the local source of truth for prospects, calls, scrape status, and export endpoints
- `.mcp.json`: project-level MCP config for Claude Code
- `plugins/gmapprospect-local/`: repo-local Codex plugin scaffold
- `plugins/gmapprospect-local/scripts/mcp_server.py`: FastMCP bridge that talks to `server.py`
- `plugins/gmapprospect-local/skills/gmapprospect-workflow/SKILL.md`: short workflow guidance for agents
- `.agents/plugins/marketplace.json`: local Codex marketplace entry for the plugin

### Exposed agent tools

The MCP bridge exposes these business tools:

- `ping_backend`
- `start_scrape`
- `get_scrape_status`
- `search_prospects`
- `get_prospect_stats`
- `update_prospect`
- `list_calls`
- `get_call_stats`
- `create_call`

### How it works

The flow is:

1. the agent calls the local MCP server
2. the MCP server checks whether `server.py` is reachable on `http://127.0.0.1:8000`
3. if needed, it tries to start `server.py`
4. it then calls the existing HTTP API endpoints
5. the agent receives clean JSON results instead of scraping terminal output

This keeps the project light:

- no external SaaS layer
- no duplicated business logic
- no need to expose raw ad hoc URLs to the model
- the existing backend remains the single source of truth

### Claude Code

Claude Code reads the project `.mcp.json` file automatically for project-scoped MCP servers.

Useful command:

```bash
claude mcp get gmapprospect-local
```

If the config is loaded correctly, Claude can use the local MCP server to:

- launch a scrape
- inspect prospects
- update lead status and notes
- read call history and call stats

### Codex

The repo also contains a local Codex plugin scaffold in:

```text
plugins/gmapprospect-local
```

It includes:

- plugin metadata in `.codex-plugin/plugin.json`
- local MCP wiring in `plugins/gmapprospect-local/.mcp.json`
- a local marketplace entry in `.agents/plugins/marketplace.json`

### Logs

If the MCP bridge has to auto-start the backend, startup output is written to:

```text
.claude/gmapprospect-server.log
```

## Generated data

Data is stored locally inside the project directory:

- `prospects.db`: primary local database used by the web app and API
- `prospects.json`: intermediate aggregated prospect store used during imports
- `results.csv`: legacy/raw scraper CSV output kept for compatibility

`.gitignore` already ignores:

- `prospects.db`
- `prospects.json`

## Recommended workflow

1. Run `python3 server.py`
2. Open `http://localhost:8000`
3. Start a scrape
4. Review imported leads in the dashboard or via `/swipe`
5. Move promising leads to the `Interested` status
6. Use `/prospection` to handle calls
7. Review completed calls in `/history`
8. Use `Export CSV` from the app when you need a cleaned export from the database

## Call history

When a call is completed from the `/prospection` page, the app stores:

- the called lead
- the note taken during the call
- the start date
- the end date
- the call duration

This data is visible on the `/history` page, with:

- the total number of calls
- the cumulative time
- the average time per call
- the detailed list of completed calls

## Important

- Scraping depends on a browser launched locally via Playwright.
- This project is designed to run **on the user's computer**.
- The local web app and export flow work from `prospects.db`, not from `results.csv`.
- If you share this repo on GitHub, each person can use it locally without you hosting a centralized service.
- Google Maps can change its HTML or tighten anti-bot protections, so some selectors may break over time.

## Useful commands

Install / update dependencies:

```bash
pip install -r requirements.txt
python3 -m playwright install chromium
```

Run the app:

```bash
python3 server.py
```

Run a direct scrape:

```bash
python3 main.py -s "plumbers in London" -t 15
```

## Current limitations

- scraping depends on the current Google Maps structure
- some leads may be incomplete
- Google protections may slow down or block some runs
- the interface is local, not multi-user

## License

See [LICENSE](LICENSE).
