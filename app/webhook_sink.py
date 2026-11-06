#!/usr/bin/env python3
"""📬 Webhook sink: receives Grafana alert notifications and prints them nicely.

A WEBHOOK is just an HTTP POST that one system sends to a URL you gave it, when something
happens ("hey, an alert is firing, here is the JSON"). That's all this tiny server is: a URL
that accepts POSTs and prints them. In real life that URL would be Slack, PagerDuty, Teams...

Watch it with:  kubectl -n pizza logs -f deploy/webhook-sink
Any path works, so you can tell contact points apart:  /kitchen  /pager  /whatever
"""
import json, time
from http.server import BaseHTTPRequestHandler, HTTPServer

ICON = {"firing": "🔥 FIRING", "resolved": "✅ RESOLVED"}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            d = json.loads(body)
        except Exception:
            print(f"[{self.path}] raw: {body[:200]!r}", flush=True)
            d = {}
        print(f"\n===== 📬 {time.strftime('%H:%M:%S')}  channel={self.path}  "
              f"status={ICON.get(d.get('status'), d.get('status'))}  "
              f"({len(d.get('alerts', []))} alert(s)) =====", flush=True)
        for a in d.get("alerts", []):
            l, an = a.get("labels", {}), a.get("annotations", {})
            print(f"  {ICON.get(a.get('status'), a.get('status'))}  {l.get('alertname')}  "
                  f"severity={l.get('severity', '-')}  pod={l.get('pod', '-')}", flush=True)
            if an.get("summary"):
                print(f"     summary: {an['summary']}", flush=True)
            if an.get("description"):
                print(f"     description: {an['description']}", flush=True)
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    do_GET = lambda self: (self.send_response(200), self.end_headers(), self.wfile.write(b"webhook sink ready\n"))

if __name__ == "__main__":
    print("📬 webhook sink listening on :8080", flush=True)
    HTTPServer(("0.0.0.0", 8080), H).serve_forever()
