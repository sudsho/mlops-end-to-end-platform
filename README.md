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

## Quickstart

```
make install
docker compose up -d                # postgres, redis, mlflow, prefect, dashboard
mlops project new --name churn      # already provisioned, this is just the cmd
mlops train --project churn
mlops register --project churn --metric roc_auc --threshold 0.7
mlops deploy --project churn --target staging
mlops status
```

## Status

Active. See `_planning/notes.md` for what is rough.
