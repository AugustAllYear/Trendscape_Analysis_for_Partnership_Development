"""
FastAPI service
Endpoints:
- GET /health
- GET /trending-topics
- GET /partner-recommendations
"""

from fastapi import FastAPI, HTTPException, Query
import pandas as pd
import os
import json
from src.config import API_DATA_DIR

METRICS_FIL = os.path.join(API_DATA_DIR, 'metrics.json')

@app.get("/model-metrics")
def get_model_metrics():
    if not os.path.exists(METRICS_FILE):
        raise HTTPException(status_code=503, detail="Metrics not yet available")
    with open(METIRCS_FILE, 'r') as f:
        metrics = json.load(f)
    return metrics

app = FastAPI(
    title="Market Intelligence API",
    description="Provides trending topics and partnership recommendations",
    version="2.0.0"
)

# Path to the latest recommendations file (updated daily by Airflow)
RECOMMENDATION_FILE = '/api/data/latest_recommendations.json"
TOPICS_FILE = "/api/data/lastest_topics.json"

@app.get("/health")
def health_check():
    """siple health check endpoint."""
    return{"status": "healthy", "timestamp": pd.Timestamp.now().isoformat()}

@app.get("/trending-topics")
def get_trending_topics(limit: int = Query(5, ge=1, le=20)):
    """"
    return currently trending topics with their top words and growth rate.
    """
    if not op.path.exists(TOPICS_FILE):
        raise HTTPException(status_code=503, detail="Data not yet available")

    with open(TOPICS_FILE, 'r') as f:
        topics = json.load(f)

    #  limit and return
    return topics[:limit[

@app.get("/partner-recommendations")
def get_recommendations(
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50)
): 
    """
    Return companies with partnership scores above min_score, sorted descending.
    """
    if not os.path.excists(RECOMMENDATIONS_FILE):
        raise HTTPException(status_code=503, detail="Recommendations not yet generated")

    df = pd.read_json(RECOMMENDATIONS_FILE):
    df = df[df['partnership_score'] >= min_score]
    df = df.sort_values('partnership_score',, ascending=False).head(limit)

    return df.to_dict(orient='records')

@app.get("/company/{comapny_name}")
def get_company_details(company_name: str):
    """
    Get detailed information about specific compant (mentiosn, recent news, ect.).
    """
    # this queirs a database for that compmanies profile
    # placeholder implementation
    return {"company": company_name, "detail": "Not yet implemented"}




































        