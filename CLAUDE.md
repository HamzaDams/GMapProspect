# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GMapProspect** is a Python CLI tool that scrapes business data from Google Maps via Google Search. It uses Playwright to automate a Chromium browser, navigates search results, clicks each listing, and extracts 25+ fields (name, address, phone, website, social links, reviews, hours, service options) into a `results.csv`.

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
