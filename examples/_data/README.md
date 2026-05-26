# shared example data

`make_synthetic.py` generates the three datasets used by the example
projects (churn, fraud, recommender). It is deterministic per seed.

```
python examples/_data/make_synthetic.py --format parquet
python examples/_data/make_synthetic.py --format parquet --drift  # post-drift fraud batch
```
