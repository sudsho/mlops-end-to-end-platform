# recommender (example project)

Homepage ranker. Daily retraining. ~80 QPS for online scoring.

- Data: synthetic clickstream, user/item features
- Features: user_engagement_30d, item_popularity, content_match, ...
- Target: `clicked`
- Metric: NDCG@10 (modeled here as a binary classifier and ranked at serve time)
