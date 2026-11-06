#!/usr/bin/env bash
# Port-forwards everything you need. Ctrl-C stops all of it.
source "$(dirname "$0")/common.sh"
trap 'kill 0' EXIT
$K -n monitoring port-forward svc/kps-grafana 3000:80 >/dev/null &
$K -n monitoring port-forward svc/kps-prometheus 9090:9090 >/dev/null &
$K -n pizza port-forward svc/pizzeria 8080:8080 >/dev/null &
say "Grafana    http://localhost:3000  (admin / pizza)"
say "Prometheus http://localhost:9090"
say "Pizzeria   http://localhost:8080  (try /metrics and /chaos?mode=fire)"
wait
