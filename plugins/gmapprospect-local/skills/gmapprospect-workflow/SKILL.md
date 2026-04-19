---
name: gmapprospect-workflow
description: Use the local GMapProspect MCP tools to launch scrapes, inspect leads, and manage call follow-up from the repo backend.
---

# GMapProspect Workflow

Use this skill when the user wants to operate the local GMapProspect project through Codex instead of manually clicking around the UI.

## Available tools

- `ping_backend`: verify backend access and auto-start `server.py` if allowed
- `start_scrape`: launch a new scrape from a search term and desired volume
- `get_scrape_status`: inspect running scrape progress and logs
- `search_prospects`: filter leads by text, status, query, and pagination
- `get_prospect_stats`: summarize prospect pipeline counts
- `update_prospect`: update lead status, notes, or contacted timestamp
- `list_calls`: inspect call history
- `get_call_stats`: summarize call activity
- `create_call`: write a call log and mark the lead as contacted

## Working style

- Start with `ping_backend` if backend availability is uncertain.
- Use `start_scrape` only when the user clearly asked for a new scrape.
- Prefer `search_prospects` before updating a lead so you confirm the right `prospect_id`.
- Use `update_prospect` for CRM state changes and `create_call` when a real call record should exist.
- When summarizing results, highlight top leads, missing websites, strong review counts, and outreach status.

## Notes

- The MCP server talks to the existing `server.py` backend.
- If the backend is down, the plugin will try to start it locally and log startup output to `.claude/gmapprospect-server.log`.
