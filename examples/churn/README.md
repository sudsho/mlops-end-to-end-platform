# churn (example project)

Telco churn classifier. Daily batch retraining. Low online QPS (~10).

- Data: synthetic Telco-style table with ~50k customers in `data/`
- Features: 14 columns, mostly tenure, plan, monthly charges
- Target: `churned` boolean
- Metric: ROC-AUC on holdout
