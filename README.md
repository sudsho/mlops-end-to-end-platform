# mlops-end-to-end-platform

End-to-end MLOps platform that ties together feature store, training,
model registry, serving, monitoring and a status dashboard so that
multiple ML projects (churn, fraud, recommender) can run side by side
on a shared stack.

## Why

Most "MLOps" projects on github are a single model in a single docker
container with a Dockerfile and a CI badge. That is not MLOps, that is
just deployment. A real MLOps platform has to handle:

- offline + online feature serving with strong point-in-time correctness
- experiment tracking + a model registry with promotion policy
- declarative training/retraining schedules with drift triggers
- serverless or k8s-native model serving
- production-grade monitoring (data drift, concept drift, latency, errors)
- a single pane of glass to see what the heck is going on

This repo wires up Feast, MLflow, Prefect, KServe, Evidently, Prometheus
and Grafana into one platform that runs three example projects
concurrently.

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
              - drift-triggered retraining

           serving:
              - KServe InferenceService per project
              - transformer wraps online feature lookup + predict
```

## Components

| Component         | Tech                       |
| ----------------- | -------------------------- |
| Feature store     | Feast 0.43 + Postgres + Redis |
| Orchestrator      | Prefect 3                  |
| Registry          | MLflow 2.20                |
| Serving           | KServe + custom transformer |
| Drift / monitoring| Evidently 0.6 + Prometheus |
| Visualisation     | Grafana 11                 |
| Dashboard         | FastAPI + HTML (Streamlit alt available) |
| CLI               | Click 8                    |

## Example projects

Three projects share the platform:

1. **churn** — telco churn classifier, daily batch retrain, low traffic
2. **fraud** — card fraud, near-real-time scoring, drift watch hourly
3. **recommender** — homepage ranker, multi-armed pipeline, A/B tested

Each example lives under `examples/<project>/` with its own data,
training script, and feature view definitions. They all register with
the same MLflow tracking server and serve through the same KServe
namespace.

## Prereqs

- Python 3.12
- Docker + docker compose
- (optional) a kube cluster with KServe installed for real serving;
  otherwise the local stack runs everything except KServe and falls
  back to a FastAPI shim for inference

## Quickstart

```
cp .env.example .env
make install
docker compose up -d                # postgres, redis, mlflow, prefect, dashboard
mlops project new --name churn      # already provisioned, this is just the cmd
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
mlops drift --project <p>               # ad-hoc drift check (also runs hourly)
mlops status                            # show all projects + their state
```

## Repo layout

```
src/
  cli/                # click cli
  feature_store/      # feast wrapper + feature definitions
  orchestrator/       # prefect flows
  registry/           # mlflow client + promotion policy
  serving/            # kserve manifests + transformer
  monitoring/         # evidently + prometheus exporter
  dashboard/          # fastapi + html
examples/
  churn/
  fraud/
  recommender/
infra/
  terraform/          # rds, elasticache, s3, ecs (prefect), eks (kserve)
  prometheus/
  grafana/
configs/platform.yaml
tests/
notebooks/walkthrough.ipynb
scripts/{bootstrap,deploy,demo}.sh
```

## Results so far

Running all three projects on the same stack:

| Project    | Train freq | Online QPS | Drift checks | Latest ROC-AUC |
| ---------- | ---------- | ---------- | ------------ | -------------- |
| churn      | daily      | ~10        | hourly       | 0.84           |
| fraud      | hourly     | ~250       | hourly       | 0.93           |
| recommender| daily      | ~80        | daily        | 0.78 (NDCG@10) |

Baseline numbers from the first clean run live in
`examples/_data/baseline_metrics.json` and are what the registry
promotion policy compares against. New runs above the threshold get
auto-promoted to staging; below, auto-rejected.

End-to-end demo: `bash scripts/demo.sh`. The script trains all three,
registers winners, deploys, and pushes a synthetic drifted batch to
trigger retraining of the fraud project.

### Screenshots

| Where                          | What you see                                    |
| ------------------------------ | ----------------------------------------------- |
| dashboard (`localhost:8080`)   | per-project state, last run, drift score, QPS  |
| MLflow (`localhost:5000`)      | runs, params, metrics, registered models       |
| Prefect (`localhost:4200`)     | flow runs, schedules, drift triggers           |
| Grafana (`localhost:3000`)     | eval metric history + inference latency        |

(screenshots in `docs/screenshots/` once I take them after the next demo run.)

## Status

Active. See `_planning/notes.md` for what is rough.
