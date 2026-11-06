# Lab 4 - The Great Pizza Fire 🔥 (~10 min)

You're on call. A teammate (or you, with your eyes closed) runs:

```bash
./scripts/chaos.sh random
```

It silently picks **one of three failures** on **one of two pods**: `fire`, `slow`, or `rush`.

## Your mission

Fill this in. Start from the dashboard and zoom in.

| Question | Your answer |
|----------|-------------|
| Which symptom changed first? (metric) | |
| Which pod is misbehaving? | |
| What do the logs say? | |
| Which failure mode is it? (`fire` / `slow` / `rush`) | |
| How did you know? | |

## Detective hints

| Failure | What you'll see |
|---------|----------------|
| `fire`  | burnt ratio up, oven temperature climbing, error logs |
| `slow`  | p95 bake time up, **no** errors |
| `rush`  | queue depth jumps, order rate spikes |

Stuck? Look at one pod vs. the other: `sum by (pod) (...)`.

## Fix it

```bash
./scripts/chaos.sh off
```

Watch the metrics recover. 🎉

## Play again

Pair up: one person runs `chaos.sh random` while the other looks away. Swap. Fastest diagnosis wins pizza.

**Next:** turn this pain into an alert → the [`grafana-alerting-lab`](https://github.com/professordiogodev/grafana-alerting-lab).
