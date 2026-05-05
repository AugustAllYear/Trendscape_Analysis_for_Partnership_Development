"""
DAG: market_intelligence_pipeline

This Airflow DAG orchestrates the daily market intelligence workflow:
1. Fetch news articles and Reddit posts from APIs.
2. Clean and preprocess the text.
3. Store cleaned data into SQLite for query optimization practice.
4. Train/update the BERTopic model.
5. Generate partnership recommendations.
6. Log results and metrics to MLflow.
"""

import os
import sys
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import joblib

# Add src to Python path before importing local modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from config import STAGING_PATH, PROCESSED_PATH, MODELS_DIR, OUTPUT_DIR, API_DATA_DIR

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# Custom modules
from data_fetchers import fetch_news_api, fetch_reddit_posts
from preprocessing import clean_text, extract_entities
from topic_model import update_topic_model, find_hottest_topic
from scoring import score_companies

# Define database path (outside of src)
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/trendscape.db')

default_args = {
    'owner': 'data_science',
    'depends_on_past': False,
    'email': ['augustvollbrecht@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 10, 7),
}

dag = DAG(
    'market_intelligence_pipeline',
    default_args=default_args,
    description='Daily market intelligence',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['market_research', 'nlp'],
)

def fetch_news(**context):
    """Fetch news from NewsAPI."""
    api_key = Variable.get("NEWSAPI_KEY")
    df = fetch_news_api(api_key, days_back=1)
    path = f"{STAGING_PATH}/news_{context['ds']}.parquet"
    df.to_parquet(path)
    context['task_instance'].xcom_push(key='news_path', value=path)
    return f"Fetched {len(df)} news articles"

def fetch_reddit(**context):
    """Fetch Reddit posts."""
    client_id = Variable.get("REDDIT_CLIENT_ID")
    client_secret = Variable.get("REDDIT_CLIENT_SECRET")
    df = fetch_reddit_posts(client_id, client_secret,
                            subreddits=['technology', 'startups', 'business'])
    path = f"{STAGING_PATH}/reddit_{context['ds']}.parquet"
    df.to_parquet(path)
    context['task_instance'].xcom_push(key='reddit_path', value=path)
    return f"Fetched {len(df)} Reddit posts"

def preprocess(**context):
    """Combine and clean data."""
    ti = context['task_instance']
    news_path = ti.xcom_pull(key='news_path', task_ids='fetch_news')
    reddit_path = ti.xcom_pull(key='reddit_path', task_ids='fetch_reddit')

    df1 = pd.read_parquet(news_path)
    df2 = pd.read_parquet(reddit_path)
    df = pd.concat([df1, df2], ignore_index=True)

    df['clean_text'] = (df['title'].fillna('') + ' ' + df['content'].fillna(''))
    df['clean_text'] = df['clean_text'].apply(clean_text)
    df['entities'] = df['clean_text'].apply(extract_entities)

    out_path = f"{PROCESSED_PATH}/clean_{context['ds']}.parquet"
    df.to_parquet(out_path)
    ti.xcom_push(key='clean_path', value=out_path)
    return "Preprocessing complete"

def store_to_sqlite(**context):
    """Store cleaned data into SQLite database for SQL query practice."""
    ti = context['task_instance']
    clean_path = ti.xcom_pull(key='clean_path', task_ids='preprocess')
    if not clean_path:
        raise ValueError("No clean data path found.")
    df = pd.read_parquet(clean_path)

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Connect to SQLite (creates file if not exists)
    conn = sqlite3.connect(DB_PATH)

    # Store the articles (append new data, avoiding duplicates by URL)
    # Use a temporary in‑memory table for efficient insert
    df[['url', 'title', 'content', 'source', 'published_at']].to_sql(
        "temp_articles", conn, if_exists="replace", index=False
    )
    conn.execute("""
        INSERT OR IGNORE INTO articles (url, title, content, source, published_at)
        SELECT url, title, content, source, published_at FROM temp_articles
    """)
    conn.execute("DROP TABLE temp_articles")

    # Create index if not already present
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
    conn.commit()
    conn.close()

    return f"Stored {len(df)} rows into SQLite at {DB_PATH}"

def update_model(**context):
    """Retrain topic model on recent data."""
    model = update_topic_model(data_path=PROCESSED_PATH, window_days=90)
    model_path = f"{MODELS_DIR}/latest_topic_model.pkl"
    joblib.dump(model, model_path)
    context['task_instance'].xcom_push(key='model_path', value=model_path)
    return "Model updated"

def score(**context):
    """Score companies using latest model."""
    ti = context['task_instance']
    model_path = ti.xcom_pull(key='model_path', task_ids='update_model')
    clean_path = ti.xcom_pull(key='clean_path', task_ids='preprocess')

    model = joblib.load(model_path)
    df = pd.read_parquet(clean_path)

    hot_topic = find_hottest_topic(model, df, lookback_days=30)
    if hot_topic == -1:
        return "No hot topic found"

    recommendations = score_companies(model, df, hot_topic, our_company_name="YourCompany")
    out_csv = f"{OUTPUT_DIR}/recommendations_{context['ds']}.csv"
    recommendations.to_csv(out_csv, index=False)
    recommendations.to_json(f"{API_DATA_DIR}/latest_recommendations.json", orient='records')
    return "Scoring complete"

# Define tasks
t1 = PythonOperator(task_id='fetch_news', python_callable=fetch_news, provide_context=True, dag=dag)
t2 = PythonOperator(task_id='fetch_reddit', python_callable=fetch_reddit, provide_context=True, dag=dag)
t3 = PythonOperator(task_id='preprocess', python_callable=preprocess, provide_context=True, dag=dag)
t3_sql = PythonOperator(task_id='store_to_sqlite', python_callable=store_to_sqlite, provide_context=True, dag=dag)
t4 = PythonOperator(task_id='update_model', python_callable=update_model, provide_context=True, dag=dag)
t5 = PythonOperator(task_id='score', python_callable=score, provide_context=True, dag=dag)

# Set dependencies
[t1, t2] >> t3 >> t3_sql >> t4 >> t5