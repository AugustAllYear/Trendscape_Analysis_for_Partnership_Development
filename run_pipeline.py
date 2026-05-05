#!/usr/bin/env python
"""
Full Trendscape pipeline – no Airflow required.
Runs: fetch → preprocess → store to SQLite → topic model → score → export.
"""

import os
import sys
import pandas as pd
import numpy as np
import sqlite3
import joblib
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import project modules
from data_fetchers import fetch_news_api, fetch_reddit_posts
from preprocessing import clean_text, extract_entities
from topic_model import update_topic_model, find_hottest_topic
from scoring import score_companies
from config import STAGING_PATH, PROCESSED_PATH, MODELS_DIR, OUTPUT_DIR, API_DATA_DIR

# Create directories
os.makedirs(STAGING_PATH, exist_ok=True)
os.makedirs(PROCESSED_PATH, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(API_DATA_DIR, exist_ok=True)

def fetch_data():
    """Fetch news and Reddit data; fallback to synthetic if keys missing."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("NEWSAPI_KEY")
        reddit_id = os.getenv("REDDIT_CLIENT_ID")
        reddit_secret = os.getenv("REDDIT_CLIENT_SECRET")
        if api_key and reddit_id and reddit_secret:
            print("Fetching real data...")
            news = fetch_news_api(api_key, days_back=1)
            reddit = fetch_reddit_posts(reddit_id, reddit_secret,
                                        subreddits=['technology','startups','business'])
            df = pd.concat([news, reddit], ignore_index=True)
            print(f"Fetched {len(df)} real articles.")
            return df
        else:
            raise ValueError("Missing API keys")
    except Exception as e:
        print(f"Real data failed ({e}). Falling back to synthetic data.")
        return generate_synthetic_data(500)

def generate_synthetic_data(n=500):
    """Synthetic data generator (same as populate_db.py)."""
    np.random.seed(42)
    titles = [
        "AI startup raises $50M for generative video",
        "Blockchain technology gains traction in supply chain",
        "New sustainability platform launched by EcoCorp",
        "TechGlobal announces quantum computing breakthrough",
        "HealthPlus acquires wellness app for $200M",
        "WorkAnywhere expands remote work tools",
        "GreenEnergy partners with major utility provider",
        "CloudNine reports 40% revenue growth",
        "AI Solutions introduces ethical AI framework",
        "WellnessInc launches mental health platform"
    ]
    sources = ["NewsAPI", "Reddit"]
    dates = [datetime.now() - timedelta(days=np.random.randint(0, 90)) for _ in range(n)]
    data = []
    for i in range(n):
        title = np.random.choice(titles)
        content = title + " Detailed description here."
        data.append({
            'url': f"http://example.com/{i}",
            'title': title,
            'content': content,
            'source': np.random.choice(sources),
            'published_at': dates[i]
        })
    return pd.DataFrame(data)

def preprocess_data(df):
    """Apply text cleaning and entity extraction."""
    print("Preprocessing text...")
    df['clean_text'] = (df['title'].fillna('') + ' ' + df['content'].fillna('')).apply(clean_text)
    df['entities'] = df['clean_text'].apply(extract_entities)
    return df

def store_to_sqlite(df, db_path="data/trendscape.db"):
    """Store articles into SQLite (same schema as DAG)."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            source TEXT,
            published_at TIMESTAMP
        )
    """)
    df[['url', 'title', 'content', 'source', 'published_at']].to_sql(
        "temp_articles", conn, if_exists="replace", index=False
    )
    conn.execute("""
        INSERT OR IGNORE INTO articles (url, title, content, source, published_at)
        SELECT url, title, content, source, published_at FROM temp_articles
    """)
    conn.execute("DROP TABLE temp_articles")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
    conn.commit()
    conn.close()
    print(f"Stored {len(df)} rows into {db_path}")

def main():
    print("=== Trendscape Full Pipeline (No Airflow) ===\n")

    # 1. Fetch data
    df = fetch_data()

    # 2. Preprocess
    df = preprocess_data(df)

    # 3. Store to SQLite (for SQL practice)
    store_to_sqlite(df)

    # 4. Train/update topic model
    print("Training BERTopic model on recent data...")
    # We need to save the processed data to a Parquet file (required by update_topic_model)
    processed_file = os.path.join(PROCESSED_PATH, "clean_manual.parquet")
    df.to_parquet(processed_file)
    model = update_topic_model(data_path=PROCESSED_PATH, window_days=90)
    model_path = os.path.join(MODELS_DIR, "latest_topic_model.pkl")
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

    # 5. Score companies
    print("Scoring companies for hottest topic...")
    hot_topic = find_hottest_topic(model, df, lookback_days=30)
    if hot_topic == -1:
        print("No hot topic found.")
        return
    recommendations = score_companies(model, df, hot_topic, our_company_name="YourCompany")
    out_csv = os.path.join(OUTPUT_DIR, f"recommendations_{datetime.now().strftime('%Y%m%d')}.csv")
    recommendations.to_csv(out_csv, index=False)
    recommendations.to_json(os.path.join(API_DATA_DIR, "latest_recommendations.json"), orient='records')
    print(f"Recommendations saved to {out_csv} and {API_DATA_DIR}/latest_recommendations.json")
    print("\nPipeline complete. You can now start:")
    print("  - FastAPI: uvicorn api.main:app --reload --port 8000")
    print("  - Streamlit: streamlit run dashboard.py")

if __name__ == "__main__":
    main()