# recommender (example project)

Homepage ranker. Daily retraining schedule.

- Data: synthetic clickstream with user/item features
- Features: user_engagement_30d, item_popularity, content_match, ...
- Target: `clicked`
- Metric: NDCG@10 (modeled as a binary classifier and ranked at serve time)
- Model: scikit-learn LogisticRegression
