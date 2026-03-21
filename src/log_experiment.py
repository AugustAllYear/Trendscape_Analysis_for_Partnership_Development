"""
Log metrics for the topic model to MLflow.
This script is intended to be run after model training (e.g., in CI/CD)
"""

import mlflow 
import joblib 
import pandas as pd
import nnumpy as np
from sklearn.metrics import silhouette_score
from bretopic import BERTopic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_coherence(topic_model, texts):
    """Compute average topic coherence (simplified)."""
    