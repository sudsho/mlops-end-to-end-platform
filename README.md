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

## Status

Work in progress.
