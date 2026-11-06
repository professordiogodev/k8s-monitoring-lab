#!/usr/bin/env python3
"""Generates dashboards/pizzeria.json (kept as code so the diff is readable)."""
import json
P = {"type": "prometheus", "uid": "prometheus"}
L = {"type": "loki", "uid": "loki"}
pid = 0
def panel(type_, title, x, y, w, h, targets, ds, unit=None, extra=None, opts=None):
    global pid; pid += 1
    p = {"id": pid, "type": type_, "title": title, "gridPos": {"x": x, "y": y, "w": w, "h": h},
         "datasource": ds, "targets": [dict(t, datasource=ds, refId=chr(65 + i)) for i, t in enumerate(targets)],
         "fieldConfig": {"defaults": {"unit": unit} if unit else {}, "overrides": []}, "options": opts or {}}
    if extra: p["fieldConfig"]["defaults"].update(extra)
    return p
red_green = {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 0.05}, {"color": "red", "value": 0.2}]}
temp_steps = {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 300}, {"color": "red", "value": 400}]}
panels = [
  panel("stat", "🍕 Pizzas / sec", 0, 0, 6, 4, [{"expr": "sum(rate(pizzeria_orders_total[1m]))"}], P, "ops"),
  panel("stat", "🔥 Burnt ratio", 6, 0, 6, 4, [{"expr": "sum(rate(pizzeria_orders_total{status=\"burnt\"}[1m])) / sum(rate(pizzeria_orders_total[1m]))"}], P, "percentunit",
        {"thresholds": red_green, "color": {"mode": "thresholds"}}),
  panel("gauge", "🌡️ Oven temperature", 12, 0, 6, 4, [{"expr": "pizzeria_oven_temperature_celsius", "legendFormat": "{{pod}}"}], P, "celsius",
        {"min": 0, "max": 600, "thresholds": temp_steps, "color": {"mode": "thresholds"}}),
  panel("stat", "⏳ Queue depth", 18, 0, 6, 4, [{"expr": "sum(pizzeria_queue_depth)"}], P),
  panel("timeseries", "Orders by status (rate)", 0, 4, 12, 8, [{"expr": "sum by (status) (rate(pizzeria_orders_total[1m]))", "legendFormat": "{{status}}"}], P, "ops"),
  panel("timeseries", "p95 bake time per pizza", 12, 4, 12, 8, [{"expr": "histogram_quantile(0.95, sum by (pizza, le) (rate(pizzeria_order_duration_seconds_bucket[1m])))", "legendFormat": "{{pizza}}"}], P, "s"),
  panel("timeseries", "Error logs / min (from LOGS, via Loki)", 0, 12, 12, 7,
        [{"expr": "sum by (pod) (count_over_time({namespace=\"pizza\"} | json | level=\"error\" [1m]))", "legendFormat": "{{pod}}"}], L),
  panel("logs", "Live pizzeria logs", 12, 12, 12, 7, [{"expr": "{namespace=\"pizza\"} | json"}], L, opts={"enableLogDetails": True, "sortOrder": "Descending", "wrapLogMessage": False}),
]
dash = {"uid": "pizzeria", "title": "🍕 Pizzeria", "tags": ["lab"], "timezone": "browser", "schemaVersion": 39, "version": 1,
        "refresh": "5s", "time": {"from": "now-15m", "to": "now"}, "panels": panels}
json.dump(dash, open("dashboards/pizzeria.json", "w"), indent=2)
print("wrote dashboards/pizzeria.json")
