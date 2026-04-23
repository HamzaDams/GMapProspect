# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GMapProspect** is a local Google Maps lead generation and prospecting tool. It uses Playwright to scrape business data, imports leads into a local SQLite-backed web app, and exposes CRM workflows for services, opportunity ranking, outreach, calls, and exports.

## MCP Usage

When the task is about running scrapes, listing prospects, managing services, ranking opportunities, updating lead status, or reading call history, prefer the project MCP server `gmapprospect-local` over ad hoc shell commands. It exposes the existing `server.py` backend and can auto-start it if needed.

For prospect prioritization, use the MCP flow:

1. `list_services`
2. `get_opportunities` with the chosen `service_id`
3. use the returned `score`, `reasons`, and `pitch_angle` to explain lead fit
4. optionally call `update_prospect` to assign the service or mark selected leads as `interested`

Do not manually re-rank raw prospects when `get_opportunities` can answer the task. The deterministic score lives in `server.py`; the LLM should add strategy, wording, and call preparation on top.

## Setup & Usage

**Requirements:** Python < 3.10 (3.9 recommended) due to dependency constraints.

```bash
pip install -r requirements.txt
playwright install chromium   # only needed once
```

**Run:**
```bash
python main.py -s "restaurants in Paris" -t 20
```

- `-s` / `--search`: search query (e.g., business type + location)
- `-t` / `--total`: number of listings to scrape (defaults to 1)

Output is written to `results.csv` in the working directory.

## Architecture

Single-file design (`main.py`, ~500 lines). No classes — all state is kept in 38+ global lists (one per field), populated in a loop, then assembled into a pandas DataFrame at the end.

**Execution flow:**
1. Launch Chromium (non-headless) via Playwright
2. Search Google → click "More locations" to reach Maps panel
3. Scroll through result cards to collect listing elements
4. For each listing: click → extract fields via XPath/CSS selectors → append to global lists
5. Handle pagination ("Next page" button)
6. Build DataFrame, drop single-value columns, export to CSV

**XPath selectors are brittle** — they depend on Google's current HTML structure and will break with UI updates. No try/catch around individual field extractions; use `element.count() > 0` checks before accessing.

## Key Implementation Details

- Address parsing splits on commas, assuming 4 tokens (street, area, zip, country) or 5 (with "Located In"). This logic is fragile for non-US addresses.
- Review counts normalize "K" suffix (e.g., "1.2K" → 1200).
- Service options (in-store, pickup, delivery) are detected via two separate XPath branches — both must be checked.
- Timeouts between actions: `page.wait_for_timeout(1000–5000)` — adjust if scraping is flaky.
- The script runs with a visible browser window (not headless) — do not change this without testing, as some Google anti-bot checks behave differently in headless mode.
