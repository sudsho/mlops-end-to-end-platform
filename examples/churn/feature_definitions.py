"""Feast feature view definitions for the churn project.

Features come from a daily snapshot in postgres + a streaming source for
realtime fields (last_call, last_payment).
"""
from datetime import timedelta

from feast import Entity, FeatureView, Field, PostgreSQLSource
from feast.types import Float32, Int64, String

customer = Entity(
    name="customer_id",
    join_keys=["customer_id"],
    description="A telco customer",
)

snapshot_source = PostgreSQLSource(
    name="churn_snapshot_source",
    query="SELECT * FROM churn_snapshot",
    timestamp_field="event_ts",
)

churn_features = FeatureView(
    name="churn_features",
    entities=[customer],
    ttl=timedelta(days=2),
    source=snapshot_source,
    schema=[
        Field(name="tenure_months", dtype=Int64),
        Field(name="monthly_charges", dtype=Float32),
        Field(name="total_charges", dtype=Float32),
        Field(name="contract_type", dtype=String),
        Field(name="internet_service", dtype=String),
        Field(name="payment_method", dtype=String),
        Field(name="num_support_calls_30d", dtype=Int64),
        Field(name="num_late_payments_90d", dtype=Int64),
        Field(name="auto_pay", dtype=Int64),
        Field(name="paperless_billing", dtype=Int64),
    ],
    online=True,
)
