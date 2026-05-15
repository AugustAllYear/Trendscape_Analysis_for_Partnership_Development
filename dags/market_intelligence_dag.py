"""
DAG: market_intelligence_pipeline
Orchestrates daily data ingestion, preprocessing, topic modeling, and SQL benchmarks.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
import pandas as pd
import joblib

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# Local modules (ensure these exist in src/)
from advanced_data_fetchers import DataFetcher
from preprocessing import clean_text, extract_entities
from topic_model import update_topic_model, find_hottest_topic
from scoring import score_companies
from db_setup import get_db_path, create_unified_schema, insert_articles_from_df
from config import STAGING_PATH, PROCESSED_PATH, MODELS_DIR, OUTPUT_DIR, API_DATA_DIR
from sql_optimization import benchmark_query_performance

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
for path in [STAGING_PATH, PROCESSED_PATH, MODELS_DIR, OUTPUT_DIR, API_DATA_DIR]:
    os.makedirs(path, exist_ok=True)

default_args = {
    'owner': 'data_science',
    'depends_on_past': False,
    'email': ['augustvollbrecht@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 5, 15),   # recent date to avoid backfill
}

dag = DAG(
    'market_intelligence_pipeline',
    default_args=default_args,
    description='Daily market intelligence with multi‑source data',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['market_research', 'nlp', 'sql_optimization'],
)

def fetch_all_data(**context):
    """Fetch data from all sources; skip failing sources gracefully."""
    fetcher = DataFetcher()
    dfs = []
    sources = [
        ('Hacker News', fetcher.fetch_hacker_news),
        ('Reddit RSS', fetcher.fetch_reddit_rss),
        ('NewsAPI', lambda: fetcher.fetch_newsapi(days_back=1)),
        ('SauravKanchan', lambda: fetcher.fetch_sauravkanchan_news(limit=50)),
        ('Lemmy', lambda: fetcher.fetch_lemmy_posts(limit=50))
    ]
    for name, func in sources:
        try:
            df = func()
            if not df.empty:
                dfs.append(df)
                logger.info(f"Fetched {len(df)} rows from {name}")
            else:
                logger.warning(f"No data from {name}")
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
    if not dfs:
        raise ValueError("No data fetched from any source. Check API keys or network.")
    combined = pd.concat(dfs, ignore_index=True)
    combined['published_at'] = pd.to_datetime(combined['published_at'], errors='coerce')
    staging_path = f"{STAGING_PATH}/all_sources_{context['ds']}.parquet"
    combined.to_parquet(staging_path)
    context['task_instance'].xcom_push(key='raw_data_path', value=staging_path)
    return f"Fetched {len(combined)} articles from all sources"

def preprocess(**context):
    """Clean text and extract entities."""
    ti = context['task_instance']
    raw_path = ti.xcom_pull(key='raw_data_path', task_ids='fetch_all_data')
    df = pd.read_parquet(raw_path)
    # Fill missing content
    df['content'] = df['content'].fillna('')
    df['title'] = df['title'].fillna('')
    df['clean_text'] = (df['title'] + ' ' + df['content']).apply(clean_text)
    df['entities'] = df['clean_text'].apply(extract_entities)
    out_path = f"{PROCESSED_PATH}/clean_{context['ds']}.parquet"
    df.to_parquet(out_path)
    ti.xcom_push(key='clean_path', value=out_path)
    return "Preprocessing complete"

def store_to_sqlite(**context):
    """Store cleaned data into SQLite using unified schema."""
    ti = context['task_instance']
    clean_path = ti.xcom_pull(key='clean_path', task_ids='preprocess')
    df = pd.read_parquet(clean_path)
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    create_unified_schema(conn)
    insert_articles_from_df(conn, df)
    conn.close()
    return f"Stored {len(df)} rows into {db_path}"

def train_model(**context):
    """Retrain topic model on recent data (last 90 days)."""
    model = update_topic_model(data_path=PROCESSED_PATH, window_days=90)
    model_path = f"{MODELS_DIR}/latest_topic_model.pkl"
    joblib.dump(model, model_path)
    context['task_instance'].xcom_push(key='model_path', value=model_path)
    return "Model updated"

def score_companies_task(**context):
    """Score companies using the hottest topic."""
    ti = context['task_instance']
    model_path = ti.xcom_pull(key='model_path', task_ids='train_model')
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

def sql_benchmark(**context):
    """Run SQL performance benchmarks and log results."""
    try:
        results = benchmark_query_performance()
        context['task_instance'].xcom_push(key='sql_benchmark', value=results)
        logger.info("SQL Benchmark Results: %s", results)
        return "Benchmark completed"
    except Exception as e:
        logger.error(f"SQL benchmark failed: {e}")
        return "Benchmark failed"

# Task definitions
t_fetch = PythonOperator(
    task_id='fetch_all_data',
    python_callable=fetch_all_data,
    provide_context=True,
    dag=dag
)
t_preprocess = PythonOperator(
    task_id='preprocess',
    python_callable=preprocess,
    provide_context=True,
    dag=dag
)
t_store = PythonOperator(
    task_id='store_to_sqlite',
    python_callable=store_to_sqlite,
    provide_context=True,
    dag=dag
)
t_train = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    provide_context=True,
    dag=dag
)
t_score = PythonOperator(
    task_id='score_companies',
    python_callable=score_companies_task,
    provide_context=True,
    dag=dag
)
t_benchmark = PythonOperator(
    task_id='sql_benchmark',
    python_callable=sql_benchmark,
    provide_context=True,
    dag=dag
)

# Dependencies
t_fetch >> t_preprocess >> t_store >> t_train >> t_score >> t_benchmark