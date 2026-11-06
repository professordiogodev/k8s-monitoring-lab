# Lab 0 - Install the stack (~10 min, mostly waiting)

## Prerequisites

- A local Kubernetes cluster (tested on **OrbStack**; Docker Desktop, kind, minikube also work)
- `kubectl`, `helm` (v3.12+)
- ~4 GB of free RAM for the cluster

Check your cluster:

```bash
kubectl config get-contexts
kubectl --context orbstack get nodes     # OrbStack: `orb start k8s` if it's not running
```

> Scripts use the `orbstack` kube-context by default. On another cluster run
> `export CTX=docker-desktop` (or `kind-kind`, `minikube`, ...) first.
> They only touch the `monitoring` and `pizza` namespaces.

## Install

```bash
./scripts/up.sh
```

It installs three Helm releases in the `monitoring` namespace and the app in `pizza`:

| Helm release | What                                                       |
|--------------|------------------------------------------------------------|
| `kps`        | Prometheus Operator, Prometheus, Grafana, node-exporter, kube-state-metrics |
| `loki`       | Loki, single binary                                        |
| `alloy`      | Grafana Alloy DaemonSet, ships container logs to Loki      |

## Check it

```bash
kubectl -n monitoring get pods
kubectl -n pizza get pods
```

Everything should be `Running`. Then in a **spare terminal**:

```bash
./scripts/pf.sh
```

| What       | URL                    | Login          |
|------------|------------------------|----------------|
| Grafana    | http://localhost:3000  | admin / pizza  |
| Prometheus | http://localhost:9090  |                |
| Pizzeria   | http://localhost:8080  |                |

✅ **Done when:** `curl localhost:8080/metrics | head` prints pizzeria metrics.

## Stuck?

- `ImagePullBackOff`: first run pulls ~1 GB of images. Be patient.
- Prometheus shows no pizzeria target: give the operator ~30s to reload the config.
- Port already in use: stop whatever uses 3000/9090/8080.
