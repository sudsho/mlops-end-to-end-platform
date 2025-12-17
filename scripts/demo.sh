#!/usr/bin/env bash
# Demo: run all three example projects on the platform end to end.
#   1. ensure stack is up
#   2. generate synthetic data
#   3. apply feast definitions
#   4. train all three projects
#   5. register + apply promotion policy
#   6. render and apply (if kubectl present) inference services
#   7. push a drifted batch for fraud and watch the drift flow trigger retrain
set -euo pipefail

cd "$(dirname "$0")/.."

bash scripts/bootstrap.sh

python examples/_data/make_synthetic.py --format parquet

for proj in churn fraud recommender; do
    pushd "examples/$proj/feature_repo" >/dev/null
    feast apply || echo "feast apply for $proj skipped (server down?)"
    popd >/dev/null
done

for proj in churn fraud recommender; do
    mlops train --project "$proj"
    mlops register --project "$proj" --metric roc_auc --threshold 0.7
    mlops deploy --project "$proj" --target staging
done

# Trigger drift on fraud and run the drift flow
python -c "
from examples._data.make_synthetic import fraud
df = fraud(n=4000, drift=True)
df.to_parquet('examples/fraud/data/current.parquet', index=False)
"

mlops drift --project fraud
echo "demo complete. open http://localhost:8080"
