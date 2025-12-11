"""Feast feature view definitions for the recommender project.

User-side and item-side features. Joined on (user_id, item_id) at training
and serving time.
"""
from datetime import timedelta

from feast import Entity, FeatureView, Field, PostgreSQLSource
from feast.types import Float32, Int64, String

user = Entity(name="user_id", join_keys=["user_id"])
item = Entity(name="item_id", join_keys=["item_id"])

user_source = PostgreSQLSource(
    name="rec_user_features_source",
    query="SELECT * FROM rec_user_features",
    timestamp_field="event_ts",
)

item_source = PostgreSQLSource(
    name="rec_item_features_source",
    query="SELECT * FROM rec_item_features",
    timestamp_field="event_ts",
)

rec_user_features = FeatureView(
    name="rec_user_features",
    entities=[user],
    ttl=timedelta(hours=24),
    source=user_source,
    schema=[
        Field(name="user_clicks_30d", dtype=Int64),
        Field(name="user_engagement_30d", dtype=Float32),
        Field(name="user_session_len_avg", dtype=Float32),
        Field(name="user_country", dtype=String),
        Field(name="user_age_bucket", dtype=String),
    ],
    online=True,
)

rec_item_features = FeatureView(
    name="rec_item_features",
    entities=[item],
    ttl=timedelta(hours=24),
    source=item_source,
    schema=[
        Field(name="item_popularity_24h", dtype=Float32),
        Field(name="item_category", dtype=String),
        Field(name="item_age_days", dtype=Int64),
        Field(name="item_avg_dwell_s", dtype=Float32),
    ],
    online=True,
)

# combined view used by the model. Joined on user_id + item_id.
rec_features = FeatureView(
    name="rec_features",
    entities=[user, item],
    ttl=timedelta(hours=24),
    source=user_source,
    schema=[
        Field(name="user_clicks_30d", dtype=Int64),
        Field(name="user_engagement_30d", dtype=Float32),
        Field(name="item_popularity_24h", dtype=Float32),
        Field(name="content_match", dtype=Float32),
    ],
    online=True,
)
