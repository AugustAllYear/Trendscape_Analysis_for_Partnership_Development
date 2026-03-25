#!/usr/bin/env python
"""
Log topic model metrics to MLflow.
Run this after training the model (e.g., in CI/CD).
"""

import mlflow
import joblib
import pandas as pd
import numpy as np
import os
import glob
import json
import logging
from bertopic import BERTopic
from gensim.corpora import Dictionary
from gensim.models.coherencemodel import CoherenceModel
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_coherence(topic_model, texts):
    """
    Compute c_v coherence for the topic model.
    """
    topics = topic_model.get_topics()
    # Exclude outlier topic -1
    topic_words = [words for tid, words in topics.items() if tid != -1]
    if not topic_words:
        return 0.0

    tokenized_texts = [text.split() for text in texts]
    dictionary = Dictionary(tokenized_texts)
    # Filter extremes to keep vocabulary manageable
    dictionary.filter_extremes(no_below=2, no_above=0.9)

    cm = CoherenceModel(topics=topic_words,
                        texts=tokenized_texts,
                        dictionary=dictionary,
                        coherence='c_v')
    coherence = cm.get_coherence()
    return coherence

def main():
    # Paths from environment or defaults
    data_path = os.getenv('DATA_PATH', './data')
    processed_path = os.path.join(data_path, 'processed')
    model_path = os.getenv('MODEL_PATH', './models/latest_topic_model.pkl')
    api_data_path = os.getenv('API_DATA_PATH', './api/data')
    os.makedirs(api_data_path, exist_ok=True)

    # Load model
    try:
        topic_model = joblib.load(model_path)
    except FileNotFoundError:
        logger.error("Model not found at %s", model_path)
        return

    # Load the most recent processed data
    files = sorted(glob.glob(f"{processed_path}/clean_*.parquet"))
    if not files:
        logger.error("No clean data files found in %s", processed_path)
        return
    latest_file = files[-1]
    df = pd.read_parquet(latest_file)
    texts = df['clean_text'].tolist()

    # Transform
    topics, probs = topic_model.transform(texts)

    # Metrics
    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    outlier_ratio = np.mean(np.array(topics) == -1)
    avg_prob = np.mean(np.max(probs, axis=1))
    coherence = compute_coherence(topic_model, texts)

    # Log to MLflow
    with mlflow.start_run(run_name="market_intelligence_eval"):
        mlflow.log_metric("n_topics", n_topics)
        mlflow.log_metric("outlier_ratio", outlier_ratio)
        mlflow.log_metric("avg_topic_probability", avg_prob)
        mlflow.log_metric("coherence_c_v", coherence)
        mlflow.sklearn.log_model(topic_model, "topic_model")

    # Save metrics JSON for API
    metrics = {
        "n_topics": n_topics,
        "outlier_ratio": outlier_ratio,
        "avg_topic_probability": avg_prob,
        "coherence_c_v": coherence,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    metrics_file = os.path.join(api_data_path, "metrics.json")
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f)

    logger.info("Logged evaluation metrics to MLflow and saved to %s", metrics_file)

if __name__ == "__main__":
    main()