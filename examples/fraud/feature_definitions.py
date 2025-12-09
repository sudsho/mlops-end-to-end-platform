"""Feast feature view definitions for the fraud project.

Two views: per-card aggregates (last hour) and per-merchant aggregates.
"""
from datetime import timedelta

from feast import Entity, FeatureView, Field, PostgreSQLSource
from feast.types import Float32, Int64, String

card = Entity(name="card_id", join_keys=["card_id"])
merchant = Entity(name="merchant_id", join_keys=["merchant_id"])

card_source = PostgreSQLSource(
    name="card_aggregates_source",
    query="SELECT * FROM card_aggregates",
    timestamp_field="event_ts",
)

merchant_source = PostgreSQLSource(
    name="merchant_aggregates_source",
    query="SELECT * FROM merchant_aggregates",
    timestamp_field="event_ts",
)

fraud_features = FeatureView(
    name="fraud_features",
    entities=[card],
    ttl=timedelta(hours=2),
    source=card_source,
    schema=[
        Field(name="amount", dtype=Float32),
        Field(name="amount_zscore_1h", dtype=Float32),
        Field(name="num_tx_1h", dtype=Int64),
        Field(name="num_unique_merchants_1h", dtype=Int64),
        Field(name="time_since_last_tx_s", dtype=Int64),
        Field(name="card_present", dtype=Int64),
        Field(name="cross_border", dtype=Int64),
        Field(name="merchant_category", dtype=String),
    ],
    online=True,
)

merchant_features = FeatureView(
    name="merchant_features",
    entities=[merchant],
    ttl=timedelta(hours=6),
    source=merchant_source,
    schema=[
        Field(name="merchant_fraud_rate_24h", dtype=Float32),
        Field(name="merchant_volume_24h", dtype=Float32),
        Field(name="merchant_category", dtype=String),
    ],
    online=True,
)
