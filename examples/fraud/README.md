# fraud (example project)

Card fraud classifier. Hourly retraining schedule with hourly drift check.

- Data: synthetic transactions from `examples/_data/make_synthetic.py`
- Features: amount, merchant_category, time_since_last_tx, is_card_present, ...
- Target: `is_fraud`
- Metric: ROC-AUC
- Model: scikit-learn LogisticRegression with `class_weight='balanced'`
