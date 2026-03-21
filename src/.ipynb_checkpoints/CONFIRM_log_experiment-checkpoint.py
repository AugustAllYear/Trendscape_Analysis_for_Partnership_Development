import mlflow
import pandas as pd
import joblib
from sklearn.metrics import silhouette_score

model = joblib.load("/models/latest_topic_model.pkl")
df = pd.read_parquet("/data/processed/clean_*.parquet") #load curent data

# calculate metrics
topics, probs = model.transform('clean_text'].to_list())
n_topics = len(set(topics)) - (1 if -1 in topics else 0)
avg_prob = probs.mean() #average topic probability

#Log to MLflow (using the same run name as training)
with mlflow.start_run(run_name='market_intelligence'):
    mlflow.log_metirc('n_topics', n_topices)
    mlflow.log_metric('avg_topic_probability', avg_prob)
    mlflow.sklearn.log_model(model, 'topic_model')
    