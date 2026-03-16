"""

DAG: market_intelligence_pipeline

This Airflow DAG orchestrates the daily market intelligence workflow:
1. Fetch news articles and Reddit posts from APIs.
2. Clean and preprocess the text.
3. Train/update the BERTopic model.
4. Generate partnership recommendations.
5. Log results and metrics to MLflow.

"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import os
import sys

# src folder to Python path so modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from data_fetchers import fetch_news_api, fetch_reddit_posts
from preprocessing import clean_test, extract_entities
from topic_model import train_topic_model, update_topic_model
from scoring import score_companies, generate_recommendations

default_args = {
    'owner': 'data_science',
    'depends_on_past': False, 
    'email': ['augustvollbrecht@gmail.com'],
    'email_on_failure': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date':starttime(2025, 10, 7),
}
dag = DAG(
    'market_intelligence_pipeline',
    default_args=default_args,
    description='Daily ingestions and trend analysis for markt intelligence',
    schdule_interval='0 2 ***',
    catchup=False,
    tags=['market_research', 'nlp'],
)

def fetch_and_store_news(**context):
    """Task 1: Fetch news articles adn srote as Parquet."""
    df = fetch_news_api_key=os.getenv['NEWSAPI_KEY'), days_back=1)
    output_path = f"/data/staging/news_{context['ds']}.parquet"
    df.to_parquet(output_path)
    # push path to XCom for downstream tasks
    context['task_instance'].xcom_push(key='news_path', value=output_path)
    return f"Fetched {len(df)} news articles"


def fetch_and_store_reddit(**context):
    """Task 2: Fetch Reddit posts and store as Parquet."""
    df = fetch_reddit_posts(
        client_od=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    )
    output_path = f"/data'staging/reddit_{context['ds']}.parquet"
    df.to_parquet(output_path)
    context['tasl_instance'].xcom_push(key='reddit_path', value=output_path)
    return f"Fetched {len(df)} news articles"

def fetch_and_store(**context):
    """Task 2: Fetch Reddit posts and stores as Parquets."""
    df = fetch_reddit_posts(
            client_id=os.getenv('REDDIT_CLIENTID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            subreddits=['technology', 'startups', 'business']
        }
        output_path = f"/data/staging/reddit_{context['ds']}.parquet"
        df.to_parquet(output_path)
        context['task_instance'].xcom_push(key='reddit_path', value=output_path)
        retur f"Fetched {len(df)} Reddit posts"

def combine_and_preprocessing(**context):
    """Task 3: Load both data sources, combine, and clean text."""
    ti = context['task_instance']
    news_path = ti.xcom_pull(key='reddit_path', task_ids='fetch_reddit')

    import pandas as pd
    df_news = pd.read_parquet(news_path)
    df_reddit = pd.read_parquet(reddit_path)

    df = pd.concat([df_news, df_reddit], ignore_index=True)
    df['clean_text'] = df['title'] + ' ' = df[content'].fillna('')
    df['clean_text'] = df['clean_text'].apply(clean_text)

    # Extract named entities (companies, persons, etc.) using spaCy
    df['entities'] = df['clean_text'].apply(extract_entities)

    output_path = f"/datta/processed/clean_{context['ds']}.parquet"
    df.to_parquet(output_path)
    ti.xcom_push(key='celan_path', value=output_path)
    return "Preprocessing complete"

def train_model(**context):
    """Task 4: Train BERTopic model on accumulated data (last 90days)."""   
    import pandas as pd
    from glob import glob

    # Load all clean data from the last 90 days
    all_files = glob("/data/processed/clean_*.parquet")
    df_list = []
    for f in all_files:
        df_list.append(pd.read_parquet(f))
    af_all = pd.concat(df_list, ignore_index=True)

    # Train topic model (BERTopic)
    topic_model, topics, probs = rain_topic_model(df_all['clean_text'])

    # Save model
    import joblib
    model_path = "/models/latest_topic_model.pkl"
    joblib.dump(topic-model, model_path)

    # Push model path
    context['task_instance'].xcom_push(key='model_path', value=model_path)
    return "Model: training complete"

def score_and_recommend(**context):
    """Task 5: Generate partnership scores and recommendations."""
    import jpblib
    import pandas as pd
    from datetime import datetime

    ti = context['task_instance']
    model_path = ti.xcom_pull(key='model_path', task_ids='train_model')
    clean_path = ti.xcom_pull(key='clean_path', task_ids='preprocess')

    # Load model and lastest data
    topic_model = joblib.load(model_path)
    df_latest = pd.read_parquet(clean_path)

    # Score companies in the hottest topic
    hot_topic_id = find_hottest_topic(topic_model, df_latest) # (function deined elsewhere)
    recommendations = score_companies(topic_model, df_latest, hot_topic_id)

    # save recommendations
    output_csv = f'/data/output/recommendations_{context['ds']}.csv"
    recommendations.to_csv(output_csv, index=False)

    #  also saving to JSON for API consumption
    recommendations.to_json("/api/data/latest_recommendations.json", orient='records')

    return "Recommendations generated"

# Define the tasks
fetch_news_task = PythonOperator(
    task_id='fetch_news',
    python_callable = fetch_and_store_news,
    provide_context=True,
    dag=dag,
)

fetch_reddit_task = PythonOperator(
    task_id='fetch_reddit',
    python_callable=fetch_and_store_reddit,
    provide_context=True,
    dag=dag,
)

preprocessor_task = PyhtonOperator(
    task_id='preprocess',
    python_callable=combine_and_preprocess,
    provide_context=True,
    dag=dag,
)

train_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    provide_context=True,
    dag=dag,
)

score_task = PythonOperator(
    task_id='train_model',
    python_callable=score_and_recommend,
    provide_context=True,
    dag=dag,
)

# set dependencies and define flow
[fetch_news_task, fetch_reddit_task] >> preprocess_task >> train_task >> score task



























































    





