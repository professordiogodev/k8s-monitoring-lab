#!/usr/bin/env python3
"""🍕 Pizzeria - a tiny, dependency-free app that makes monitoring fun.

It bakes fake pizzas in the background, exposes Prometheus metrics on /metrics
and writes JSON logs to stdout. You can break the oven on purpose with /chaos.

Endpoints:
  /metrics            Prometheus metrics
  /healthz            liveness
  /chaos?mode=MODE    MODE = off | slow | fire | rush
  /                   status page
"""
import itertools, json, os, random, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PIZZAS = ["margherita", "pepperoni", "hawaiian", "quattro-formaggi", "diavola"]
BUCKETS = [0.1, 0.25, 0.5, 1, 2.5, 5, 10]
LOCK = threading.Lock()
IDS = itertools.count(1)

state = {"chaos": os.environ.get("CHAOS", "off"), "queue": 0, "temp": 250.0}
# initialise every series at 0 so rate()/ratios never come back empty (good practice!)
orders = {(p, st): 0 for p in PIZZAS for st in ("ok", "burnt", "failed")}
hist = {p: [0] * len(BUCKETS) for p in PIZZAS}
hist_sum = {p: 0.0 for p in PIZZAS}
hist_count = {p: 0 for p in PIZZAS}


def log(level, msg, **kw):
    print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "level": level,
                      "msg": msg, **kw}), flush=True)


def bake(order_id):
    pizza = random.choice(PIZZAS)
    mode = state["chaos"]
    started = time.monotonic()
    # base bake time ~ 0.2-1.2s, with an occasional slow pizza (long tail, like real life)
    work = random.uniform(0.2, 1.2) + (random.uniform(1, 2) if random.random() < 0.05 else 0)
    if mode == "slow":
        work *= random.uniform(3, 6)
    status = "ok"
    if mode == "fire" and random.random() < 0.6:
        status = "burnt"
    elif random.random() < 0.02:          # background noise: 2% always fail
        status = "failed"
    time.sleep(work)
    duration = time.monotonic() - started  # MEASURED time, not a made-up number
    with LOCK:
        orders[(pizza, status)] = orders.get((pizza, status), 0) + 1
        for i, b in enumerate(BUCKETS):
            if duration <= b:
                hist[pizza][i] += 1
        hist_sum[pizza] += duration
        hist_count[pizza] += 1
    if status == "ok":
        log("info", "pizza served", order_id=order_id, pizza=pizza,
            duration_ms=int(duration * 1000))
    elif status == "burnt":
        log("error", "pizza is burnt, the oven is on fire", order_id=order_id,
            pizza=pizza, oven_temp=round(state["temp"]))
    else:
        log("warn", "order failed, customer left angry", order_id=order_id, pizza=pizza)


def kitchen():
    while True:
        mode = state["chaos"]
        with LOCK:
            state["queue"] = random.randint(0, 3) + (25 if mode == "rush" else 0)
            target = 480 if mode == "fire" else 250
            state["temp"] += (target - state["temp"]) * 0.1 + random.uniform(-4, 4)
        bake(next(IDS))
        time.sleep(0.05 if mode == "rush" else random.uniform(0.1, 0.5))


def render_metrics():
    out = ["# HELP pizzeria_orders_total Pizzas baked, by outcome.",
           "# TYPE pizzeria_orders_total counter"]
    with LOCK:
        for (p, s), v in sorted(orders.items()):
            out.append(f'pizzeria_orders_total{{pizza="{p}",status="{s}"}} {v}')
        out += ["# HELP pizzeria_order_duration_seconds Time to bake a pizza.",
                "# TYPE pizzeria_order_duration_seconds histogram"]
        for p in PIZZAS:
            for i, b in enumerate(BUCKETS):
                out.append(f'pizzeria_order_duration_seconds_bucket{{pizza="{p}",le="{b}"}} {hist[p][i]}')
            out.append(f'pizzeria_order_duration_seconds_bucket{{pizza="{p}",le="+Inf"}} {hist_count[p]}')
            out.append(f'pizzeria_order_duration_seconds_sum{{pizza="{p}"}} {hist_sum[p]:.3f}')
            out.append(f'pizzeria_order_duration_seconds_count{{pizza="{p}"}} {hist_count[p]}')
        out += ["# HELP pizzeria_oven_temperature_celsius Oven temperature.",
                "# TYPE pizzeria_oven_temperature_celsius gauge",
                f'pizzeria_oven_temperature_celsius {state["temp"]:.1f}',
                "# HELP pizzeria_queue_depth Orders waiting.",
                "# TYPE pizzeria_queue_depth gauge",
                f'pizzeria_queue_depth {state["queue"]}']
    return "\n".join(out) + "\n"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):          # silence default access log
        pass

    def reply(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/metrics":
            self.reply(200, render_metrics(), "text/plain; version=0.0.4")
        elif u.path == "/healthz":
            self.reply(200, "ok\n")
        elif u.path == "/chaos":
            mode = parse_qs(u.query).get("mode", ["off"])[0]
            if mode not in ("off", "slow", "fire", "rush"):
                return self.reply(400, "mode must be off|slow|fire|rush\n")
            state["chaos"] = mode
            log("warn", "chaos mode changed", mode=mode)
            self.reply(200, f"🔥 chaos mode is now: {mode}\n")
        else:
            self.reply(200, f"🍕 Pizzeria is open. chaos={state['chaos']} "
                            f"oven={state['temp']:.0f}C\n")


if __name__ == "__main__":
    log("info", "pizzeria opening", chaos=state["chaos"])
    for _ in range(int(os.environ.get("COOKS", "4"))):
        threading.Thread(target=kitchen, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
