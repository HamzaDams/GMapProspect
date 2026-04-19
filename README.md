# GMapProspect

Local Google Maps scraping and sales outreach tool.

The project runs **on the user's machine**.

- run the Playwright scraper on your own computer
- store prospects locally
- review leads in dashboard or swipe mode
- handle calls in focus mode
- review call history with notes and duration

## What the project does

- scrapes Google Maps leads from a search query
- exports a `results.csv`
- fills a local `prospects.db` database
- maintains a `prospects.json` file for aggregated results
- provides several local interfaces:
  - `/`: main dashboard
  - `/swipe`: quick lead triage
  - `/prospection`: focus call mode
  - `/history`: call history

## Stack

- Python
- Playwright + Chromium
- SQLite
- HTML / CSS / JS vanilla
- local HTTP server via `server.py`

## Installation

### 1. Clone the repository

```bash
git clone <YOUR-GITHUB-REPO>
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

## Generated data

Data is stored locally inside the project directory:

- `results.csv`: CSV export of the latest scrape
- `prospects.json`: JSON aggregation of prospects
- `prospects.db`: local SQLite database

`.gitignore` already ignores:

- `prospects.db`
- `prospects.json`

## Recommended workflow

1. Run `python3 server.py`
2. Open `http://localhost:8000`
3. Start a scrape
4. Qualify leads from the dashboard or via `/swipe`
5. Move promising leads to the `Interested` status
6. Use `/prospection` to handle calls
7. Review completed calls in `/history`

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
