# mlops-end-to-end-platform

Reference MLOps platform that wires up feature store, training,
model registry, serving scaffolding, monitoring hooks and a status
dashboard so that multiple example ML projects (churn, fraud,
recommender) can share one stack.

Treat this repo as an architecture scaffold, not a benchmarked or
production deployment.

## Quick start (runs offline)

The full platform (Feast, Prefect, KServe on k8s, Postgres, Redis, S3,
Prometheus, Grafana) is heavy. To prove the core model lifecycle without
any of that, there is an offline smoke that runs on CPU with no keys, no
downloads, no docker, and no cloud. It exercises the real platform code
(`registry.client`, `registry.policy`, `monitoring.drift`) against local
backends: a synthetic pandas frame stands in for Feast, a local MLflow
file store (`file:./mlruns`) is the registry, and drift falls back to a
KS / chi-square test when Evidently is not installed.

```
make smoke        # or: python scripts/smoke.py
```

Real output on a fresh checkout (Python 3.11, mlflow 2.22, scikit-learn 1.8,
no feast / evidently installed):

```
=== 0. environment ===
mlflow tracking uri : file:///.../mlops-end-to-end-platform/mlruns
feast               : not installed -> pandas feature stand-in
evidently           : not installed -> KS/chi-square drift fallback

=== 1. build features (synthetic, Feast stand-in) ===
built churn frame   : 4000 rows x 13 cols
positive class rate : 0.447

=== 2. train + log to local MLflow ===
run_id              : ca4e9cd500b04997a7e5cb0bcefb331d
roc_auc             : 0.7036
accuracy            : 0.6475

=== 3. register + promote ===
promoted to Staging : True (threshold roc_auc >= 0.65)
promoted to Prod    : True

=== 4. load Production model + predict ===
model uri           : models:/churn/1
predictions (5 rows): [0, 0, 0, 0, 0]

=== 5. drift: reference vs current (synthetic) ===
drift (ref vs ref)  : 0.000
drift (ref vs cur)  : 0.200
drift report        : artifacts\drift_report.html

=== SMOKE OK ===
roc_auc >= 0.65       : True
staged + produced   : True
drift detected      : True

RESULT              : PASS
```

The lifecycle it walks: build features -> train a scikit-learn model and
log it to local MLflow -> register the model, promote it to Staging on the
metric gate, then to Production -> load the Production model back and
predict -> score data drift on synthetic reference-vs-current frames and
write an HTML report. `run_id` is a fresh MLflow UUID each run; the metrics
are deterministic.

Unit tests (no docker, no cloud):

```
python -m pytest
# 12 passed, 1 skipped in ~2s
```

The one skip is a test that only runs when Evidently is installed. Feast,
Prefect, and KServe imports are all guarded, so nothing in the smoke or the
test suite needs them.

### What still needs the heavy stack

Documented but not part of the offline smoke, since they need external
services or a cluster:

- Feast online/offline store (needs Postgres + Redis): `make up`, then the
  `feature_store` wrapper.
- Prefect flows and schedules (`src/orchestrator/`): need a Prefect server.
- KServe serving (`src/serving/`): needs a k8s cluster with KServe; a local
  FastAPI shim is provided as a laptop / CI fallback.
- Prometheus + Grafana dashboards under `infra/`.

## Why

Most "MLOps" projects on github are a single model in a single docker
container with a Dockerfile and a CI badge. That is not MLOps, that is
just deployment. A more realistic MLOps platform pulls in:

- a feature store for offline + online features
- experiment tracking + a model registry with a promotion policy
- declarative training schedules
- k8s-native model serving (or a local fallback)
- monitoring hooks (data drift, latency)
- a single dashboard to see project state

This repo wires up Feast, MLflow, Prefect, KServe, Evidently, Prometheus
and Grafana into one platform scaffold and ships three example project
folders.

## Architecture

```
                    +----------------+
                    |   dashboard    |  <-- FastAPI + lightweight HTML
                    +-------+--------+
                            |
            +---------------+----------------+
            |               |                |
   +--------v-----+  +------v------+  +------v------+
   | feature      |  |  registry   |  | monitoring  |
   | store (feast)|  |  (mlflow)   |  | (evidently) |
   +-------+------+  +------+------+  +------+------+
           |                |                |
   +-------v-----+  +-------v------+  +------v-------+
   | postgres +  |  | s3 artifacts |  | prometheus + |
   | redis       |  | (offline)    |  | grafana      |
   +-------------+  +--------------+  +--------------+

           orchestrator (prefect) drives:
              - training flow
              - retraining flow

           serving:
              - KServe InferenceService manifest per project
              - local FastAPI shim for laptop / CI
```

## Components

| Component         | Tech                       |
| ----------------- | -------------------------- |
| Feature store     | Feast 0.43 + Postgres + Redis |
| Orchestrator      | Prefect 3                  |
| Registry          | MLflow 2.20                |
| Serving           | KServe manifest scaffold + local FastAPI shim |
| Drift module      | Evidently, with a KS / chi-square fallback exercised by the offline smoke |
| Metrics           | Prometheus + Grafana panels |
| Dashboard         | FastAPI + HTML (Streamlit alt available) |
| CLI               | Click 8                    |

## Example projects

Three project folders share the platform layout:

1. **churn** - telco churn classifier (scikit-learn GradientBoosting)
2. **fraud** - card fraud classifier (scikit-learn LogisticRegression, class_weight balanced)
3. **recommender** - homepage ranker (scikit-learn LogisticRegression, ranked at serve time)

Each example lives under `examples/<project>/` with its own synthetic
data generator, training script, and Feast feature view definitions.
Training scripts fall back to inline synthetic data when the data
files are absent.

## Prereqs

- Python 3.12
- Docker + docker compose
- (optional) a kube cluster with KServe installed to actually deploy
  the rendered InferenceService manifests

## Quickstart

```
cp .env.example .env
make install
docker compose up -d                # postgres, redis, mlflow, prefect, dashboard
mlops train --project churn
mlops register --project churn --metric roc_auc --threshold 0.7
mlops deploy --project churn --target staging
mlops status
```

## CLI surface

```
mlops project new --name <p>           # provision a project on the platform
mlops train --project <p>               # kick off a training run via prefect
mlops register --project <p> ...        # register the latest run with mlflow + apply policy
mlops deploy --project <p> --target <env>
mlops drift --project <p>               # ad-hoc drift check
mlops status                            # show all projects + their state
```

## Repo layout

```
src/
  cli/                # click cli
  feature_store/      # feast wrapper + feature definitions
  orchestrator/       # prefect flows
  registry/           # mlflow client + promotion policy
  serving/            # kserve manifests + transformer + local shim
  monitoring/         # evidently + prometheus exporter
  dashboard/          # fastapi + html
examples/
  churn/
  fraud/
  recommender/
infra/
  terraform/          # skeleton: rds, elasticache, s3, bare ecs + eks clusters
  prometheus/
  grafana/
configs/platform.yaml
tests/
notebooks/walkthrough.ipynb
scripts/{bootstrap,deploy,demo}.sh
```

## Scope and known gaps

This is a breadth-of-architecture scaffold. Honest caveats:

- No benchmarked results or serving throughput numbers. There is no
  load-test harness in the repo.
- Training scripts run on the small synthetic generators in
  `examples/_data/make_synthetic.py`. Numbers depend on that seed and
  are not tuned.
- The Terraform under `infra/terraform/` provisions RDS, ElastiCache,
  S3 and bare ECS + EKS clusters. There is no task definition, no
  node group, and no Helm install for KServe.
- The rendered KServe manifest references a transformer image that
  this repo does not build.
- The drift module targets the Evidently 0.7 API. When Evidently is not
  installed it falls back to a plain KS / chi-square per-feature test
  (scipy), which is the path the offline smoke uses. The Evidently path
  itself is not pinned-and-verified here.
- No CI is currently active in this repo (workflow file sits at
  `ci/test.yml.example`).

End-to-end demo: `bash scripts/demo.sh` (trains, registers, deploys,
pushes a synthetic drifted batch for the fraud project).

## Status

Reference scaffold.
