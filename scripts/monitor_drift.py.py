#!/usr/bin/env python
"""
Detect topic drift by comparing topic distributions between recent and past periods.
"""

import joblib
import pandas as pd
import numpy as np
import os
import glob
from scipy.spatial.distance import jensenshannon

def detect_drift():
    data_path = os.getenv('DATA_PATH', './data')
    processed_path = os.path.join(data_path, 'processed')
    model_path = os.getenv('MODEL_PATH', './models/latest_topic_model.pkl')

    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        print("Model not found, skipping drift detection")
        return

    files = sorted(glob.glob(f"{processed_path}/clean_*.parquet"))
    if len(files) < 2:
        print("Not enough data to detect drift")
        return

    recent_df = pd.read_parquet(files[-1])
    past_df = pd.read_parquet(files[-2])
    recent_texts = recent_df['clean_text'].tolist()
    past_texts = past_df['clean_text'].tolist()

    topics_recent, _ = model.transform(recent_texts)
    topics_past, _ = model.transform(past_texts)

    def distribution(topics):
        unique, counts = np.unique(topics, return_counts=True)
        dist = np.zeros(max(unique)+1)
        for u, c in zip(unique, counts):
            dist[u] = c
        return dist / dist.sum()

    dist_recent = distribution(topics_recent)
    dist_past = distribution(topics_past)

    js_div = jensenshannon(dist_recent, dist_past)
    print(f"Jensen-Shannon divergence: {js_div:.4f}")
    if js_div > 0.2:
        print("ALERT: Significant topic drift detected")
    else:
        print("Topic distribution stable")

if __name__ == "__main__":
    detect_drift()