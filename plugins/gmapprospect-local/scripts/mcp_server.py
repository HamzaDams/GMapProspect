#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from fastmcp import FastMCP


REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_URL = os.environ.get("GMAPPROSPECT_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
AUTOSTART = os.environ.get("GMAPPROSPECT_AUTOSTART", "1").lower() not in {"0", "false", "no"}
SERVER_START_TIMEOUT_SECONDS = 20
REQUEST_TIMEOUT_SECONDS = 20

mcp = FastMCP(
    name="GMapProspect API",
    instructions=(
        "Use these tools to run local GMapProspect scraping, inspect prospects, "
        "and manage outreach workflow through the repo backend."
    ),
)


def _healthcheck() -> bool:
    try:
        response = httpx.get(f"{BASE_URL}/api/prospects/stats", timeout=2.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def _server_bind_args() -> tuple[str, int]:
    parsed = urlparse(BASE_URL)
    host = parsed.hostname or "127.0.0.1"
    if parsed.port is not None:
        port = parsed.port
    elif parsed.scheme == "https":
        port = 443
    else:
        port = 80
    return host, port


def _start_backend() -> None:
    log_path = REPO_ROOT / ".claude" / "gmapprospect-server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    host, port = _server_bind_args()
    with log_path.open("ab") as log_file:
        subprocess.Popen(
            [
                sys.executable,
                str(REPO_ROOT / "server.py"),
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=REPO_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def ensure_backend() -> dict[str, Any]:
    if _healthcheck():
        return {"running": True, "started_now": False, "base_url": BASE_URL}

    if not AUTOSTART:
        raise RuntimeError(
            "GMapProspect backend is unreachable and autostart is disabled. "
            "Start server.py or set GMAPPROSPECT_AUTOSTART=1."
        )

    _start_backend()
    deadline = time.time() + SERVER_START_TIMEOUT_SECONDS
    while time.time() < deadline:
        if _healthcheck():
            return {"running": True, "started_now": True, "base_url": BASE_URL}
        time.sleep(0.5)

    raise RuntimeError(
        "GMapProspect backend did not start in time. "
        "Check .claude/gmapprospect-server.log for details."
    )


def request_json(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> Any:
    ensure_backend()
    response = httpx.request(
        method,
        f"{BASE_URL}{path}",
        params=params,
        json=json_body,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool(description="Return prospect counts and distinct scrape queries.")
def get_prospect_stats() -> dict[str, Any]:
    return request_json("GET", "/api/prospects/stats")


@mcp.tool(description="Search prospects with optional status, closed state, query, text search, sorting, and pagination.")
def search_prospects(
    search: str = "",
    status: str = "",
    closed: str = "",
    query: str = "",
    sort: str = "scraped_at",
    page: int = 1,
    per_page: int = 24,
) -> dict[str, Any]:
    params = {
        "sort": sort,
        "page": page,
        "per_page": per_page,
    }
    if search:
        params["search"] = search
    if status:
        params["status"] = status
    if closed:
        params["closed"] = closed
    if query:
        params["query"] = query
    return request_json("GET", "/api/prospects", params=params)


@mcp.tool(description="Start a local scrape for a search term and target result count.")
def start_scrape(search: str, total: int = 10) -> dict[str, Any]:
    if not search.strip():
        raise ValueError("search is required")
    return request_json(
        "POST",
        "/api/scrape",
        json_body={"search": search.strip(), "total": total},
    )


@mcp.tool(description="Return the current scrape status, logs, and any backend error.")
def get_scrape_status() -> dict[str, Any]:
    return request_json("GET", "/api/scrape/status")


@mcp.tool(description="Update a prospect status, notes, contacted timestamp, or closed state.")
def update_prospect(
    prospect_id: str,
    status: str = "",
    notes: str = "",
    contacted_at: str = "",
    is_closed: bool | None = None,
    closed_at: str = "",
) -> dict[str, Any]:
    if not prospect_id.strip():
        raise ValueError("prospect_id is required")

    payload: dict[str, Any] = {}
    if status:
        payload["status"] = status
    if notes:
        payload["notes"] = notes
    if contacted_at:
        payload["contacted_at"] = contacted_at
    if is_closed is not None:
        payload["is_closed"] = is_closed
        payload["closed_at"] = closed_at if is_closed else ""
    elif closed_at:
        payload["closed_at"] = closed_at

    if not payload:
        raise ValueError("At least one field must be provided to update a prospect")

    return request_json("PUT", f"/api/prospects/{prospect_id}", json_body=payload)


@mcp.tool(description="List call history with optional query filter, text search, and pagination.")
def list_calls(
    search: str = "",
    query: str = "",
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    params = {
        "page": page,
        "per_page": per_page,
    }
    if search:
        params["search"] = search
    if query:
        params["query"] = query
    return request_json("GET", "/api/calls", params=params)


@mcp.tool(description="Return aggregated call statistics and call volume by scrape query.")
def get_call_stats() -> dict[str, Any]:
    return request_json("GET", "/api/calls/stats")


@mcp.tool(description="Create a call log for a prospect, mark it as contacted, and optionally close the lead.")
def create_call(
    prospect_id: str,
    started_at: str = "",
    ended_at: str = "",
    duration_seconds: int = 0,
    notes: str = "",
    closed: bool = False,
) -> dict[str, Any]:
    if not prospect_id.strip():
        raise ValueError("prospect_id is required")

    return request_json(
        "POST",
        "/api/calls",
        json_body={
            "prospect_id": prospect_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_seconds": duration_seconds,
            "notes": notes,
            "closed": closed,
        },
    )


@mcp.tool(description="Return the backend connection status and whether it had to be started.")
def ping_backend() -> dict[str, Any]:
    return ensure_backend()


if __name__ == "__main__":
    mcp.run("stdio")
