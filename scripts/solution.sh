#!/usr/bin/env bash
# Stuck in lab 5? Load the complete alerting setup (rules, contact points, policies, mute timing) as code.
# Delete your own contact points named kitchen-log / pager and rules with the same titles first, to avoid name clashes.
source "$(dirname "$0")/common.sh"
say "Loading the alerting solution into Grafana"
$K -n monitoring create configmap alerting-solution --from-file="$ROOT/solution/alerting" --dry-run=client -o yaml | $K apply -f -
$H upgrade kps prometheus-community/kube-prometheus-stack -n monitoring \
  -f "$ROOT/helm/kps-values.yaml" -f "$ROOT/solution/kps-mount-values.yaml" --wait --timeout 8m
say "Done. Grafana restarted: re-run ./scripts/pf.sh if your port-forward dropped."
