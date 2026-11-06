# Lab 5 - Alerting in Grafana (~30 min)

Goal: get **paged when the oven catches fire**, route alerts by severity, and silence the noise. Runs on the stack from Lab 0 (nothing more to install).

Until now *you* had to look at dashboards. Nobody stares at Grafana at 3am, so let's make Grafana tap *us* on the shoulder.

```
 Prometheus ◄── alert rule (evaluated by Grafana every 10s)
 Loki       ◄──      │ fires
                     ▼
              notification policy ──► severity=critical ──► contact point "pager"
                     │
                     └─ default ───────────────────────────► contact point "kitchen-log"
                                                                   │ webhook (HTTP POST)
                                      webhook-sink pod (kubectl logs) 📬
```

## 🪝 What is a webhook?

A **webhook** is simply an **HTTP POST** that one system sends to a URL you gave it, *when something happens*.

- **Polling** (what you did in Labs 1-4): *you* keep asking "anything new?"
- **Webhook**: you give a URL once, and the system **calls you** when there is news.

Slack, PagerDuty, GitHub, Stripe, Microsoft Teams: all of them use webhooks. In Grafana, a **contact point** of type *Webhook* means: *"when this alert fires or resolves, POST a JSON to this URL"*. A trimmed example of what Grafana sends:

```json
{
  "status": "firing",
  "alerts": [{
    "status": "firing",
    "labels":      {"alertname": "Burnt pizzas", "severity": "critical", "pod": "pizzeria-abc"},
    "annotations": {"summary": "pizzeria-abc: 61% of pizzas are burnt 🔥"}
  }]
}
```

We don't have Slack here, so `app/webhook_sink.py` plays the role of the pager: a ~40-line Python server that receives these POSTs and prints them. In real life you would paste a Slack/PagerDuty/Teams URL instead and nothing else changes.

**Try it by hand** (this is literally all a webhook is):

```bash
kubectl -n pizza port-forward svc/webhook-sink 8081:8080 &
curl -X POST localhost:8081/hello -H 'Content-Type: application/json' \
  -d '{"status":"firing","alerts":[{"status":"firing","labels":{"alertname":"Demo","severity":"critical"},"annotations":{"summary":"I poked the webhook by hand"}}]}'
kill %1
```

Look at the sink's logs (next step): your fake alert is there.

## 0. Get ready (3 min)

Stack from Lab 0 up, `./scripts/pf.sh` running. In a **second** spare terminal, watch where alerts land:

```bash
kubectl -n pizza logs -f deploy/webhook-sink
```

Open Grafana: http://localhost:3000 (`admin` / `pizza`). Make sure the oven is healthy: `./scripts/chaos.sh off`.

> 🧠 Compare with Lab 1: we already have a **Prometheus** alert, `PizzaBurning` (Prometheus UI → Alerts). It goes `Firing`... and nobody hears it, because we disabled Alertmanager. Grafana alerting does the *whole* job (rules + routing + notifying) in one place, and can alert on **Loki logs too**.

## 1. Contact points (5 min)

*Alerting → Contact points → Add contact point*

| Name | Integration | URL |
|------|-------------|-----|
| `kitchen-log` | Webhook | `http://webhook-sink.pizza.svc:8080/kitchen` |
| `pager` | Webhook | `http://webhook-sink.pizza.svc:8080/pager` |

(That URL is a normal Kubernetes Service DNS name: `<service>.<namespace>.svc`.)

Press **Test** on each. A 📬 message appears in the sink logs. ✅

## 2. Your first alert rule (8 min)

*Alerting → Alert rules → New alert rule*

1. **Name**: `Burnt pizzas`
2. **Query A** (Prometheus), *Code* mode, **Instant** query:
   ```promql
   sum by (pod) (rate(pizzeria_orders_total{status="burnt"}[1m])) / sum by (pod) (rate(pizzeria_orders_total[1m]))
   ```
3. **Expressions**: *Reduce* B = last of A. *Threshold* C = B **is above** `0.2`. Make C the alert condition.
4. **Folder**: create `Pizzeria`. **Evaluation group**: `pizzeria`, interval `10s`. **Pending period**: `30s`.
5. **Labels**: `severity = critical`, `team = kitchen`
6. **Annotations → Summary**:
   ```
   {{ $labels.pod }}: {{ humanizePercentage $values.B.Value }} of pizzas are burnt 🔥
   ```
7. Leave the contact point to the *notification policy* (next step). Save.

> 💡 Because the query is `sum by (pod)`, Grafana creates **one alert instance per pod**: a multi-dimensional alert. One rule, many alerts.

## 3. Notification policy (5 min)

*Alerting → Notification policies*

- Edit the **default policy**: contact point `kitchen-log`, group by `alertname`, `pod`. Under *Timing options* set group wait `5s`, group interval `30s`.
- **Add nested policy**: label `severity` `=` `critical` → contact point `pager`.

The policy tree routes alerts by **labels**. That's why labels matter.

## 4. Light the fire (5 min)

```bash
./scripts/chaos.sh fire        # burns ONE pod
```

Watch *Alert rules* (Normal → **Pending** → **Firing**), the dashboard, and the sink logs. Within ~1.5 minutes:

```
===== 📬 12:03:41  channel=/pager  status=🔥 FIRING  (1 alert(s)) =====
  🔥 FIRING  Burnt pizzas  severity=critical  pod=pizzeria-...
     summary: pizzeria-...: 61% of pizzas are burnt 🔥
```

Only the **burnt pod** alerts. The other pod stays Normal. Now fix it and watch the ✅ RESOLVED webhook:

```bash
./scripts/chaos.sh off
```

## 5. Silence & mute (2 min)

- **Silence** (one-off): *Alerting → Silences → New*, matcher `team = kitchen`, 10 minutes. Run `chaos.sh fire` again: the alert fires but **no webhook arrives**. Remove the silence.
- **Mute timing** (recurring): *Notification policies → Mute timings → Add*: `night-shift`, 02:00 to 05:00. Attach it to the `critical` policy.

## 6. Bonus (as many as you have time for)

- **Alert on logs** (Loki): new rule, datasource **Loki**, *Instant* query
  `sum by (pod) (count_over_time({namespace="pizza"} | json | level="error" [1m]))`, threshold above `10`, `severity=warning`. Trigger with `chaos.sh fire`. This is the Lab 3 query turned into a pager.
- **Warning alert**: p95 bake time above 4s for 30s (normal is ~2s), `severity=warning`. Trigger with `./scripts/chaos.sh slow`. Which contact point receives it?
- **No data**: `kubectl -n pizza scale deploy/pizzeria --replicas=0`. What state does your rule go to? Change *No data handling* to *Alerting* and try again. Scale back to 2.

## Stuck?

```bash
./scripts/solution.sh
```

Loads the complete setup (3 rules, 2 contact points, policies, mute timing) as **code**, from `solution/alerting/`. Delete your own `kitchen-log` / `pager` contact points and same-named rules first, otherwise the names clash. Compare the YAML with what you built by hand: this is how you'd keep alerting in git.

## Good alert rules (take-away)

- Alert on **symptoms** (burnt pizzas), not causes (oven temperature)
- Every alert needs an owner, a severity, and a "what do I do" annotation
- Use the pending period (`for`) to avoid flapping; group to avoid alert storms
- If nobody acts on an alert, **delete it**

Cleanup: `./scripts/down.sh`
