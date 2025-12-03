# fraud (example project)

Card fraud classifier. Hourly retraining. Higher QPS (~250) and stricter drift watch.

- Data: synthetic transactions, ~200k rows
- Features: amount, merchant_category, time_since_last_tx, is_card_present, ...
- Target: `is_fraud`
- Metric: ROC-AUC, with class imbalance handled in training
