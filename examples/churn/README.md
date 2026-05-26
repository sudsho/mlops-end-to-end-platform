# churn (example project)

Telco churn classifier. Daily batch retraining schedule.

- Data: synthetic Telco-style table from `examples/_data/make_synthetic.py`
- Features: tenure, plan, monthly charges, etc.
- Target: `churned` boolean
- Metric: ROC-AUC on holdout
- Model: scikit-learn GradientBoostingClassifier
