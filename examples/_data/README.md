# shared example data

`make_synthetic.py` generates the three datasets used by the example
projects (churn, fraud, recommender). It is deterministic per seed.

```
python examples/_data/make_synthetic.py --format parquet
python examples/_data/make_synthetic.py --format parquet --drift  # post-drift fraud batch
```

`baseline_metrics.json` is the snapshot of the first clean training run
across the three projects. The promotion policy in `src/registry/policy.py`
uses these as the floor; anything below is auto-rejected. Update only
when you have a real reason to, and write the reason in the commit msg.
