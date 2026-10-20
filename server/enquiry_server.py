#!/usr/bin/env python3
"""viotours.in — minimal form endpoint (stdlib only).

Receives JSON POSTs from the site's forms at /api/enquiry, stores every submission in
SQLite, and optionally emails it. Run it behind nginx (see deploy/nginx.conf).

    VT_SMTP_HOST=smtp.gmail.com VT_SMTP_USER=you@gmail.com VT_SMTP_PASS=app-password \
    VT_NOTIFY_TO=hello@viotours.in python3 server/enquiry_server.py

Env vars (all optional):
    VT_PORT        port to listen on (default 8081, bound to 127.0.0.1)
    VT_DB          SQLite file (default ./leads.sqlite3)
    VT_SMTP_HOST / VT_SMTP_PORT (587) / VT_SMTP_USER / VT_SMTP_PASS / VT_NOTIFY_TO
    VT_ALLOWED_ORIGIN  e.g. https://www.viotours.in (default: same-origin only)

List leads:  python3 server/enquiry_server.py --list
"""
from __future__ import annotations

import json
import os
import smtplib
import sqlite3
import sys
import threading
import time
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("VT_PORT", "8081"))
DB = os.environ.get("VT_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.sqlite3"))
FORMS = {"trip-request", "contact", "partner", "newsletter"}
MAX_BODY = 16 * 1024
RATE: dict[str, list[float]] = {}
LOCK = threading.Lock()


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT DEFAULT (datetime('now')),
        form TEXT, name TEXT, email TEXT, phone TEXT, package TEXT, payload TEXT, ip TEXT, status TEXT DEFAULT 'new')""")
    return con


def notify(data: dict) -> None:
    host, to = os.environ.get("VT_SMTP_HOST"), os.environ.get("VT_NOTIFY_TO")
    if not host or not to:
        return
    msg = EmailMessage()
    msg["Subject"] = f"[viotours] {data.get('form')} — {data.get('name') or data.get('email') or 'new'}"
    msg["From"] = os.environ.get("VT_SMTP_USER", to)
    msg["To"] = to
    if data.get("email"):
        msg["Reply-To"] = data["email"]
    msg.set_content("\n".join(f"{k}: {v}" for k, v in data.items()))
    try:
        with smtplib.SMTP(host, int(os.environ.get("VT_SMTP_PORT", "587")), timeout=15) as s:
            s.starttls()
            if os.environ.get("VT_SMTP_USER"):
                s.login(os.environ["VT_SMTP_USER"], os.environ.get("VT_SMTP_PASS", ""))
            s.send_message(msg)
    except Exception as e:  # never lose the lead because mail failed; it's already in SQLite
        print("mail failed:", e, file=sys.stderr)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        origin = os.environ.get("VT_ALLOWED_ORIGIN")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/api/enquiry":
            return self._send(404, {"ok": False})
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        now = time.time()
        with LOCK:  # 10 submissions per IP per 10 minutes
            hits = [t for t in RATE.get(ip, []) if now - t < 600]
            if len(hits) >= 10:
                return self._send(429, {"ok": False, "error": "too many requests"})
            RATE[ip] = hits + [now]
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            return self._send(413, {"ok": False})
        try:
            data = json.loads(self.rfile.read(n))
            assert isinstance(data, dict) and data.get("form") in FORMS
        except Exception:
            return self._send(400, {"ok": False, "error": "bad request"})
        if data.get("website"):  # honeypot filled: pretend success
            return self._send(200, {"ok": True})
        data = {str(k)[:40]: str(v)[:4000] for k, v in data.items()}
        if not (data.get("email") or data.get("phone")):
            return self._send(400, {"ok": False, "error": "email or phone required"})
        with db() as con:
            con.execute("INSERT INTO leads (form,name,email,phone,package,payload,ip) VALUES (?,?,?,?,?,?,?)",
                        (data.get("form"), data.get("name") or data.get("organisation"), data.get("email"),
                         data.get("phone"), data.get("package"), json.dumps(data, ensure_ascii=False), ip))
        threading.Thread(target=notify, args=(data,), daemon=True).start()
        self._send(200, {"ok": True})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    if "--list" in sys.argv:
        for row in db().execute("SELECT id, created, form, name, email, phone, package, status FROM leads ORDER BY id DESC LIMIT 50"):
            print(" | ".join(str(c or "") for c in row))
        sys.exit()
    print(f"viotours enquiry endpoint on 127.0.0.1:{PORT}, leads -> {DB}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
