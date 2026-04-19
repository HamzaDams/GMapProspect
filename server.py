import http.server
import json
import sqlite3
import subprocess
import threading
import sys
import os
import csv
import io
import uuid
from urllib.parse import urlparse, parse_qs

DB_PATH = "prospects.db"
PORT = 8000


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id TEXT PRIMARY KEY,
            search_query TEXT,
            scraped_at TEXT,
            status TEXT DEFAULT 'to_contact',
            notes TEXT DEFAULT '',
            contacted_at TEXT DEFAULT '',
            name TEXT,
            address TEXT,
            address_line TEXT,
            area TEXT,
            zip_code TEXT,
            country TEXT,
            located_in TEXT,
            website TEXT,
            phone TEXT,
            reviews_count TEXT,
            reviews_average TEXT,
            place_type TEXT,
            opens_at TEXT,
            about TEXT,
            facebook TEXT,
            instagram TEXT,
            twitter TEXT,
            tiktok TEXT,
            linkedin TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS call_history (
            id TEXT PRIMARY KEY,
            prospect_id TEXT NOT NULL,
            prospect_name TEXT,
            phone TEXT,
            search_query TEXT,
            notes TEXT DEFAULT '',
            started_at TEXT,
            ended_at TEXT,
            duration_seconds INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(prospect_id) REFERENCES prospects(id)
        )
    """)
    conn.execute("""
        INSERT INTO call_history
        (id, prospect_id, prospect_name, phone, search_query, notes, started_at, ended_at, duration_seconds, created_at)
        SELECT
            lower(hex(randomblob(16))),
            p.id,
            p.name,
            p.phone,
            p.search_query,
            p.notes,
            p.contacted_at,
            p.contacted_at,
            0,
            p.contacted_at
        FROM prospects p
        WHERE p.status = 'contacted'
          AND p.contacted_at != ''
          AND NOT EXISTS (
              SELECT 1
              FROM call_history c
              WHERE c.prospect_id = p.id
          )
    """)
    conn.commit()
    conn.close()


scrape_status = {"running": False, "log": [], "error": None}


def run_scrape(search, total):
    scrape_status["running"] = True
    scrape_status["log"] = []
    scrape_status["error"] = None
    try:
        proc = subprocess.Popen(
            [sys.executable, "main.py", "-s", search, "-t", str(total)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        for line in proc.stdout:
            scrape_status["log"].append(line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            scrape_status["error"] = "Le script a terminé avec une erreur."
    except Exception as e:
        scrape_status["error"] = str(e)
    finally:
        # Import newly created prospects.json into SQLite
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prospects.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            conn = get_db()
            inserted = 0
            for r in records:
                existing = conn.execute("SELECT id FROM prospects WHERE name=? AND address=?", (r.get("name",""), r.get("address",""))).fetchone()
                if not existing:
                    conn.execute("""
                        INSERT OR IGNORE INTO prospects
                        (id,search_query,scraped_at,status,notes,contacted_at,name,address,address_line,area,zip_code,country,located_in,website,phone,reviews_count,reviews_average,place_type,opens_at,about,facebook,instagram,twitter,tiktok,linkedin)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        r.get("id"), r.get("search_query"), r.get("scraped_at"),
                        r.get("status","to_contact"), r.get("notes",""), r.get("contacted_at",""),
                        r.get("name"), r.get("address"), r.get("address_line"), r.get("area"),
                        r.get("zip_code"), r.get("country"), r.get("located_in"), r.get("website"),
                        r.get("phone"), str(r.get("reviews_count","")), str(r.get("reviews_average","")),
                        r.get("place_type"), r.get("opens_at"), r.get("about"),
                        r.get("facebook"), r.get("instagram"), r.get("twitter"),
                        r.get("tiktok"), r.get("linkedin")
                    ))
                    inserted += 1
            conn.commit()
            conn.close()
            scrape_status["log"].append(f"✓ {inserted} prospects importés en base.")
        scrape_status["running"] = False


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # silence default logs

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_static_page(self, filename):
        self.send_file(filename, "text/html; charset=utf-8")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_static_page("index.html")

        elif path == "/swipe" or path == "/swipe.html":
            self.send_static_page("swipe.html")

        elif path == "/prospection" or path == "/prospection.html":
            self.send_static_page("prospection.html")

        elif path == "/history" or path == "/history.html":
            self.send_static_page("history.html")

        elif path == "/api/prospects":
            conn = get_db()
            status_filter = qs.get("status", [None])[0]
            query_filter = qs.get("query", [None])[0]
            search_filter = qs.get("search", [None])[0]
            sort = qs.get("sort", ["scraped_at"])[0]
            page = int(qs.get("page", [1])[0])
            per_page = int(qs.get("per_page", [24])[0])

            sql = "SELECT * FROM prospects WHERE 1=1"
            params = []
            if status_filter:
                sql += " AND status=?"; params.append(status_filter)
            if query_filter:
                sql += " AND search_query=?"; params.append(query_filter)
            if search_filter:
                sql += " AND (name LIKE ? OR address LIKE ? OR place_type LIKE ? OR phone LIKE ?)"
                like = f"%{search_filter}%"
                params += [like, like, like, like]

            sort_map = {"name": "name ASC", "reviews_count": "CAST(reviews_count AS INTEGER) DESC", "scraped_at": "scraped_at DESC"}
            sql += f" ORDER BY {sort_map.get(sort, 'scraped_at DESC')}"

            total_count = conn.execute(f"SELECT COUNT(*) FROM ({sql})", params).fetchone()[0]
            sql += " LIMIT ? OFFSET ?"
            params += [per_page, (page - 1) * per_page]

            rows = conn.execute(sql, params).fetchall()
            conn.close()
            self.send_json({"total": total_count, "page": page, "per_page": per_page, "data": [dict(r) for r in rows]})

        elif path == "/api/prospects/stats":
            conn = get_db()
            stats = {
                "total": conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0],
                "to_contact": conn.execute("SELECT COUNT(*) FROM prospects WHERE status='to_contact'").fetchone()[0],
                "contacted": conn.execute("SELECT COUNT(*) FROM prospects WHERE status='contacted'").fetchone()[0],
                "interested": conn.execute("SELECT COUNT(*) FROM prospects WHERE status='interested'").fetchone()[0],
                "not_interested": conn.execute("SELECT COUNT(*) FROM prospects WHERE status='not_interested'").fetchone()[0],
                "queries": [r[0] for r in conn.execute("SELECT DISTINCT search_query FROM prospects WHERE search_query != '' ORDER BY search_query").fetchall()],
            }
            conn.close()
            self.send_json(stats)

        elif path == "/api/calls":
            conn = get_db()
            query_filter = qs.get("query", [None])[0]
            search_filter = qs.get("search", [None])[0]
            page = int(qs.get("page", [1])[0])
            per_page = int(qs.get("per_page", [20])[0])

            sql = "SELECT * FROM call_history WHERE 1=1"
            params = []
            if query_filter:
                sql += " AND search_query=?"
                params.append(query_filter)
            if search_filter:
                sql += " AND (prospect_name LIKE ? OR phone LIKE ? OR notes LIKE ?)"
                like = f"%{search_filter}%"
                params += [like, like, like]

            sql += " ORDER BY ended_at DESC, created_at DESC"
            total_count = conn.execute(f"SELECT COUNT(*) FROM ({sql})", params).fetchone()[0]
            sql += " LIMIT ? OFFSET ?"
            params += [per_page, (page - 1) * per_page]
            rows = conn.execute(sql, params).fetchall()
            conn.close()
            self.send_json({"total": total_count, "page": page, "per_page": per_page, "data": [dict(r) for r in rows]})

        elif path == "/api/calls/stats":
            conn = get_db()
            row = conn.execute("""
                SELECT
                    COUNT(*) AS total_calls,
                    COALESCE(SUM(duration_seconds), 0) AS total_duration_seconds,
                    COALESCE(AVG(duration_seconds), 0) AS average_duration_seconds,
                    MAX(ended_at) AS last_call_at
                FROM call_history
            """).fetchone()
            query_rows = conn.execute("""
                SELECT search_query, COUNT(*) AS calls_count
                FROM call_history
                WHERE search_query != ''
                GROUP BY search_query
                ORDER BY calls_count DESC, search_query ASC
            """).fetchall()
            conn.close()
            payload = dict(row)
            payload["queries"] = [r["search_query"] for r in query_rows]
            payload["by_query"] = [dict(r) for r in query_rows]
            self.send_json(payload)

        elif path == "/api/scrape/status":
            self.send_json(scrape_status)

        elif path == "/api/prospects/export":
            conn = get_db()
            rows = conn.execute("SELECT * FROM prospects ORDER BY scraped_at DESC").fetchall()
            conn.close()
            fields = ["name","status","phone","website","address","place_type","reviews_average","reviews_count","notes","contacted_at","search_query","scraped_at"]
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for r in rows:
                writer.writerow({f: dict(r).get(f,"") for f in fields})
            body = out.getvalue().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=prospects.csv")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/scrape":
            search = body.get("search", "").strip()
            total = int(body.get("total", 10))
            if not search:
                self.send_json({"error": "search is required"}, 400)
                return
            if scrape_status["running"]:
                self.send_json({"error": "Un scraping est déjà en cours"}, 409)
                return
            t = threading.Thread(target=run_scrape, args=(search, total), daemon=True)
            t.start()
            self.send_json({"ok": True, "message": f"Scraping lancé : {search}"})

        elif path == "/api/calls":
            prospect_id = body.get("prospect_id", "").strip()
            started_at = body.get("started_at", "")
            ended_at = body.get("ended_at", "")
            duration_seconds = int(body.get("duration_seconds", 0) or 0)
            notes = body.get("notes", "")

            if not prospect_id:
                self.send_json({"error": "prospect_id is required"}, 400)
                return

            conn = get_db()
            prospect = conn.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,)).fetchone()
            if not prospect:
                conn.close()
                self.send_json({"error": "Prospect introuvable"}, 404)
                return

            call_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO call_history
                (id, prospect_id, prospect_name, phone, search_query, notes, started_at, ended_at, duration_seconds, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id,
                prospect_id,
                prospect["name"],
                prospect["phone"],
                prospect["search_query"],
                notes,
                started_at,
                ended_at,
                duration_seconds,
                ended_at or started_at
            ))
            conn.execute("""
                UPDATE prospects
                SET status=?, notes=?, contacted_at=?
                WHERE id=?
            """, ("contacted", notes, ended_at, prospect_id))
            conn.commit()
            row = conn.execute("SELECT * FROM call_history WHERE id=?", (call_id,)).fetchone()
            conn.close()
            self.send_json(dict(row), 201)

        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        # /api/prospects/:id
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "prospects":
            pid = parts[2]
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            conn = get_db()
            allowed = ["status", "notes", "contacted_at"]
            updates = {k: v for k, v in body.items() if k in allowed}
            if updates:
                set_clause = ", ".join(f"{k}=?" for k in updates)
                conn.execute(f"UPDATE prospects SET {set_clause} WHERE id=?", list(updates.values()) + [pid])
                conn.commit()
            row = conn.execute("SELECT * FROM prospects WHERE id=?", (pid,)).fetchone()
            conn.close()
            self.send_json(dict(row) if row else {})
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    init_db()
    server = http.server.HTTPServer(("", PORT), Handler)
    print(f"GMapProspect running → http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
