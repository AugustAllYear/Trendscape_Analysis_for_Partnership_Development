"""
BERTopic model training and trend detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from glob import glob
import logging
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def train_topic_model(texts, min_topic_size=10):
    """
    Train a BERTopic model on a list of texts.
    Returns (model, topics, probabilities).
    """
    logger.info(f"Training BERTopic on {len(texts)} documents")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    topic_model = BERTopic(
        embedding_model=embedding_model,
        min_topic_size=min_topic_size,
        verbose=True,
        calculate_probabilities=True,
    )
    topics, probs = topic_model.fit_transform(texts)
    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    logger.info(f"Found {n_topics} topics")
    return topic_model, topics, probs

def update_topic_model(data_path: str = "/data/processed/", window_days: int = 90):
    """
    Retrain topic model on the most recent `window_days` of data.
    """
    # Load all parquet files
    all_files = glob(f"{data_path}/clean_*.parquet")
    if not all_files:
        raise FileNotFoundError("No clean data files found.")
    df_list = [pd.read_parquet(f) for f in all_files]
    df_all = pd.concat(df_list, ignore_index=True)

    # Filter to last `window_days`
    cutoff = datetime.now() - timedelta(days=window_days)
    df_all['published_at'] = pd.to_datetime(df_all['published_at'])
    df_recent = df_all[df_all['published_at'] > cutoff]

    if len(df_recent) < 10:
        raise ValueError(f"Not enough recent data ({len(df_recent)} docs) to train.")

    # Train new model
    new_model, _, _ = train_topic_model(df_recent['clean_text'].tolist())
    return new_model

def find_hottest_topic(topic_model, df, lookback_days=30):
    """
    Determine which topic has grown fastest in the last `lookback_days`.
    Returns topic ID.
    """
    if 'published_at' not in df.columns:
        raise ValueError("DataFrame must contain 'published_at' column")

    df = df.copy()
    df['published_at'] = pd.to_datetime(df['published_at'])
    df = df.sort_values('published_at')

    # Get topic assignments
    topics, _ = topic_model.transform(df['clean_text'].tolist())
    df['topic'] = topics

    cutoff = df['published_at'].max() - timedelta(days=lookback_days)
    recent = df[df['published_at'] > cutoff]
    baseline = df[df['published_at'] <= cutoff]

    recent_counts = recent['topic'].value_counts()
    baseline_counts = baseline['topic'].value_counts()

    growth = {}
    for topic in recent_counts.index:
        if topic == -1:
            continue
        r = recent_counts.get(topic, 0)
        b = baseline_counts.get(topic, 0)
        if b > 0:
            growth[topic] = (r - b) / b
        else:
            growth[topic] = float('inf') if r > 0 else 0

    if growth:
        hottest = max(growth.items(), key=lambda x: x[1])
        return hottest[0]
    return -1