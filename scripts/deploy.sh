#!/usr/bin/env bash
# Render KServe InferenceService manifests for each project and apply them.
# Defaults to staging. Use --target production to roll the prod stage.
set -euo pipefail

cd "$(dirname "$0")/.."

TARGET="${1:-staging}"
OUT="build/manifests"

mkdir -p "$OUT"

for proj in churn fraud recommender; do
    python -c "
from serving.render import write_inference_service
write_inference_service('$proj', '$OUT', stage='${TARGET^}')
" 2>&1 | sed "s/^/[$proj] /"
done

if command -v kubectl >/dev/null 2>&1; then
    kubectl apply -f "$OUT/" || echo "kubectl apply failed (cluster reachable?)"
else
    echo "kubectl not installed, manifests left in $OUT/"
fi
