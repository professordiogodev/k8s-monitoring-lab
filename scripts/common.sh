# shared helpers - sourced by the other scripts
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Use OrbStack's cluster by default; override with CTX=docker-desktop (or kind-xxx, minikube...)
CTX="${CTX:-orbstack}"
K="kubectl --context $CTX"
H="helm --kube-context $CTX"
say() { printf '\n\033[1;35m🍕 %s\033[0m\n' "$*"; }
for bin in kubectl helm; do command -v $bin >/dev/null || { echo "missing: $bin"; exit 1; }; done
$K cluster-info >/dev/null 2>&1 || { echo "❌ cluster for context '$CTX' is not reachable (OrbStack: 'orb start k8s')"; exit 1; }
