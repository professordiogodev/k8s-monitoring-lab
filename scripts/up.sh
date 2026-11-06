#!/usr/bin/env bash
# Installs the whole stack: Prometheus + Grafana (kube-prometheus-stack), Loki, Alloy, and the Pizzeria.
source "$(dirname "$0")/common.sh"

say "Adding helm repos"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update >/dev/null

say "1/4 Prometheus + Grafana (kube-prometheus-stack) in namespace 'monitoring'"
$H upgrade --install kps prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f "$ROOT/helm/kps-values.yaml" --wait --timeout 8m

say "2/4 Loki (single binary)"
$H upgrade --install loki grafana/loki \
  -n monitoring -f "$ROOT/helm/loki-values.yaml" --wait --timeout 8m

say "3/4 Alloy (log shipper)"
$H upgrade --install alloy grafana/alloy \
  -n monitoring -f "$ROOT/helm/alloy-values.yaml" --wait --timeout 5m

say "4/4 The Pizzeria 🍕"
$K apply -f "$ROOT/manifests/00-namespace.yaml"
$K -n pizza create configmap pizzeria-code --from-file="$ROOT/app/pizzeria.py" \
  --dry-run=client -o yaml | $K apply -f -
$K apply -f "$ROOT/manifests/10-pizzeria.yaml"
$K apply -f "$ROOT/manifests/20-servicemonitor.yaml"
$K apply -f "$ROOT/manifests/30-prometheusrule.yaml"
# the pretend pager used by lab 5
$K -n pizza create configmap webhook-sink-code --from-file="$ROOT/app/webhook_sink.py" \
  --dry-run=client -o yaml | $K apply -f -
$K apply -f "$ROOT/manifests/40-webhook-sink.yaml"
# the dashboard we ship (Grafana's sidecar auto-loads ConfigMaps labelled grafana_dashboard=1)
$K -n monitoring create configmap pizzeria-dashboard --from-file="$ROOT/dashboards/pizzeria.json" \
  --dry-run=client -o yaml | $K apply -f -
$K -n monitoring label configmap pizzeria-dashboard grafana_dashboard=1 --overwrite
$K -n pizza rollout status deploy/pizzeria deploy/webhook-sink --timeout=180s

say "Done! Next: ./scripts/pf.sh   (Grafana: http://localhost:3000  admin / pizza)"
