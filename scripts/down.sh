#!/usr/bin/env bash
# Removes everything the lab installed (only OUR namespaces/releases).
source "$(dirname "$0")/common.sh"
say "Cleaning up"
$K delete ns pizza --ignore-not-found
$H uninstall alloy -n monitoring 2>/dev/null || true
$H uninstall loki -n monitoring 2>/dev/null || true
$H uninstall kps -n monitoring 2>/dev/null || true
$K delete ns monitoring --ignore-not-found
# CRDs are cluster-wide; leave them unless you pass --crds
if [[ "${1:-}" == "--crds" ]]; then
  $K get crd -o name | grep monitoring.coreos.com | xargs -r $K delete
fi
say "Clean. 🧹"
