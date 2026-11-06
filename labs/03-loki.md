# Lab 3 - Logs with Loki (~15 min)

Grafana → **Explore** → choose the **Loki** datasource. Switch to **Code** mode for typing queries.

## 1. Find your logs (3 min)

```logql
{namespace="pizza"}
```

Click one line. Look at the labels Alloy added: `namespace`, `pod`, `container`, `app`. Compare with `helm/alloy-values.yaml` - find the `rule` blocks that create them.

Narrow down:

```logql
{namespace="pizza", pod=~"pizzeria-.*"}
{namespace="monitoring", container="grafana"}
```

## 2. Filter and parse (5 min)

Our app logs JSON. Parse it with `| json`, then filter on fields:

```logql
{namespace="pizza"} |= "served"
{namespace="pizza"} | json | level="info"
{namespace="pizza"} | json | level="info" | duration_ms > 800
```

Break something: `./scripts/chaos.sh fire`, then:

```logql
{namespace="pizza"} | json | level="error"
{namespace="pizza"} |= "on fire" | json | line_format "{{.pizza}} burnt at {{.oven_temp}}°C"
```

## 3. Logs → metrics (4 min)

LogQL can count log lines. This graph is built **from logs**:

```logql
sum by (pod) (count_over_time({namespace="pizza"} | json | level="error" [1m]))
sum by (pizza) (count_over_time({namespace="pizza"} | json | level="error" [5m]))
```

**Challenge**: which pizza burns the most? Which pod?

## 4. Metrics and logs side by side (3 min)

In Explore click **Split**. Left: Prometheus `pizzeria_oven_temperature_celsius`. Right: Loki `{namespace="pizza"} | json | level="error"`. Same time range: the temperature spike and the error logs line up.

## Why `order_id` is not a label

Each distinct label value creates a new log **stream**. `order_id` has thousands of values → thousands of streams → slow, expensive Loki. Labels should be few and low-cardinality; put everything else in the log line and filter at query time (that's what `| json` is for).

## Bonus

- `rate({namespace="pizza"}[1m])` - log lines per second per stream.
- Add an `app` label filter: `{app="pizzeria"}`.
