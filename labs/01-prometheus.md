# Lab 1 - Talk to Prometheus (~25 min)

Open http://localhost:9090 (run `./scripts/pf.sh` first).

## 1. Is the pizzeria being scraped? (3 min)

- **Status → Targets** (or *Status → Target health*): find `serviceMonitor/pizza/pizzeria/0`. It should list 2 endpoints, both `UP`.
- Raw data: `curl -s localhost:8080/metrics | head -20`. This is exactly what Prometheus reads, every 5s.

Now see *why* Prometheus scrapes it. Read the manifest and answer: **which line links the ServiceMonitor to the Service?**

```bash
cat manifests/20-servicemonitor.yaml
kubectl -n pizza get svc pizzeria --show-labels
```

<details><summary>Answer</summary>
<code>selector.matchLabels: {app: pizzeria}</code> matches the label on the Service.
</details>

## 2. First PromQL queries (7 min)

Type each in the **Graph** tab. Before you run it, guess what you will see.

```promql
up
up{namespace="pizza"}
pizzeria_orders_total
pizzeria_oven_temperature_celsius
```

Now why is `pizzeria_orders_total` a boring line going up? Because it's a **counter**. Use `rate()`:

```promql
rate(pizzeria_orders_total[1m])
sum(rate(pizzeria_orders_total[1m]))
sum by (status) (rate(pizzeria_orders_total[1m]))
sum by (pizza) (rate(pizzeria_orders_total[1m]))
```

**Challenge A** - which pizza is the best seller? (the highest `sum by (pizza)`)

## 3. Latency with histograms (5 min)

> Diogo's Todo:
> Change the pizzeria_order_duration_seconds_bucket to a more realistic value (you can skip this part)

```promql
histogram_quantile(0.95,
  sum by (le) (rate(pizzeria_order_duration_seconds_bucket[1m])))
```

**Challenge B** - show p50 and p99 too. Which bucket boundaries does the app define? (hint: look at `le` in `/metrics`)

## 4. Kubernetes metrics for free (5 min)

kube-state-metrics (object state) and node-exporter (the node itself) come with the stack:

```promql
kube_pod_status_phase{namespace="pizza", phase="Running"}
kube_deployment_status_replicas_available{namespace="pizza"}
kube_pod_container_status_restarts_total{namespace="pizza"}
kube_pod_container_resource_limits{namespace="pizza", resource="memory"}
node_load1
1 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m]))
```

> OrbStack's built-in cAdvisor doesn't export per-container CPU/memory (`container_*` metrics). On kind/minikube/real clusters you'd also get e.g. `container_memory_working_set_bytes`.

**Challenge C** - kill a pod and watch Kubernetes heal itself:

```bash
kubectl -n pizza delete pod -l app=pizzeria --wait=false
```

Graph `kube_deployment_status_replicas_available{namespace="pizza"}` and `up{namespace="pizza"}`.

🤔 **You probably saw... almost nothing.** Kubernetes replaces a deleted pod within seconds, and Prometheus only looks every 5s, so the dip is too short to catch (if at all). Look at what *did* change: the pod names in `up` are new, the old ones are gone. Healing so fast is great for users but means "the pod died" often leaves little trace in metrics. (That's why `kube_pod_container_status_restarts_total` and alerts on it matter.)

Now make a **lasting** change, so you can see Kubernetes state moving in the graphs. Rescale the deployment:

```bash
kubectl -n pizza scale deploy/pizzeria --replicas=1   # watch the numbers go DOWN
kubectl -n pizza scale deploy/pizzeria --replicas=4   # ...and UP
kubectl -n pizza scale deploy/pizzeria --replicas=2   # back to normal
```

After each command (wait ~10s), check:

```promql
kube_deployment_spec_replicas{namespace="pizza"}              # what you asked for
kube_deployment_status_replicas_available{namespace="pizza"}  # what is really running
count(up{namespace="pizza", job="pizzeria"})                  # targets Prometheus scrapes
```

Do the three lines agree right away? Which one reacts first when you scale up, and why? (hints: our pizzeria is scraped every 5s but kube-state-metrics only every 30s, and a new pod must pass its readiness probe)

## 5. Break something (5 min)

```bash
./scripts/chaos.sh fire
```

Wait ~1 minute, then:

```promql
sum by (pod) (rate(pizzeria_orders_total{status="burnt"}[1m]))
pizzeria_oven_temperature_celsius
```

Which pod is on fire? Then look at **Alerts** in the Prometheus UI: the rule `PizzaBurning` from `manifests/30-prometheusrule.yaml` goes `Pending` and then `Firing`. Read it: what do `for: 30s` and the recording rule do?

Fix everything: `./scripts/chaos.sh off`

## Bonus

- Add your own recording rule to `manifests/30-prometheusrule.yaml` and `kubectl apply` it. Check **Status → Rules**.
- Change the scrape interval to `30s`. What happens to your `rate()` graphs?
