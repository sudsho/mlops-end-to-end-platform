# mlops-end-to-end-platform

Reference MLOps platform that wires up feature store, training,
model registry, serving scaffolding, monitoring hooks and a status
dashboard so that multiple example ML projects (churn, fraud,
recommender) can share one stack.

Treat this repo as an architecture scaffold, not a benchmarked or
production deployment.

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
| Drift module      | Evidently (scaffold, not exercised end to end) |
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
- The drift module targets the Evidently 0.7 API; running it under
  the pinned 0.6 wheel will not work end to end.
- No CI is currently active in this repo (workflow file sits at
  `ci/test.yml.example`).

End-to-end demo: `bash scripts/demo.sh` (trains, registers, deploys,
pushes a synthetic drifted batch for the fraud project).

## Status

Reference scaffold.
