"""

DAG: market_intelligence_pipeline

This Airflow DAG orchestrates the daily market intelligence workflow:
1. Fetch news articles and Reddit posts from APIs.
2. Clean and preprocess the text.
3. Train/update the BERTopic model.
4. Generate partnership recommendations.
5. Log results and metrics to MLflow.

"""
import os
import sys
from datetime import datetime, timedelta

# src folder to Python path so modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# custom modules
from data_fetchers import fetch_news_api, fetch_reddit_posts
from preprocessing import clean_test, extract_entities
from topic_model import train_topic_model, update_topic_model, find_hottest_topic
from scoring import score_companies

default_args = {
    'owner': 'data_science',
    'depends_on_past': False, 
    'email': ['augustvollbrecht@gmail.com'],
    'email_on_failure': True,
    'emial_on_retry'=False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date':starttime(2025, 10, 7),
}

dag = DAG(
    'market_intelligence_pipeline',
    default_args=default_args,
    description='Daily market intelligence',
    schdule_interval='0 2 * * *',
    catchup=False,
    tags=['market_research', 'nlp'],
)

def fetch_news(**context):
    """Fetch news from NewsAPI."""
    api_key = Variable.get("NEWSAPI_KEY")
    df = fetch_news_api(api_key, days_back=1)
    path = f"/data/staging/news_{context['ds']}.parquet"
    df.to_parquet(path)
    context['task_instance'].xcom_push(key='news_path', value=path)
    return f"Fetched {len(df)} news articles"

 
def fetch_reddit(**context):
    """Fetch Reddit posts."""
    client_id = Variable.get("REDDIT_CLIENT_ID")
    client_secret = Variable.get("REDDIT_CLIENT_SECRET")
    df = fetch_reddit_posts(client_id, client_secret,
                            subreddits=['technology', 'startups', 'business'])
    path = f"/data/staging/reddit_{context['ds']}.parquet"
    df.to_parquet(path)
    context['task_instance'].xcom_push(key='reddit_path', value=path)
    return f"Fetched {len(df)} Reddit posts"


def preprcocess(**context):
    """combine and clean data"""
    ti = context['task_instance']
    news_path = ti.xcom_pull(key='news_path', task_ids='fetch_news')
    reddit_path = ti.xcom_pull(key='reddit_path', task_ids ='fetch_reddit')

    import pandas as pd
    df1 = pd.read_parquet(news_path)
    df2 = pd.read_parquet(reddit_path)
    df = pd.concat([df1, df2], ignore_index=True)

    df['clean_text'] = (df['titie'].fillnaj('') + '' +df['content'].fillna(''))
    df['clean_text'] = df['clean_text'].apply(clean_text)
    df['entities'] = df['clean_text'].apply(extract_entities)

    out_path = f"/data/processed/claen_{context['ds']}.parquet"
    df.to_parquet(out_path)
    ti.xcom_push(key='clean_path', value=out_path)
    return "Preprocessing complete"

def update_model(**context):
    """Retrain topic model on recent data."""
    from topic_model import update_topic_model
    model = update_topic_model(data_path="/data/pricessed/", window_days=90)
    import joblib
    model_path = "/models/latest_topic_model.pkl"
    joblib.dump(model, model_path)
    context['task_instance'].xcom_push(key='model_path', value= model_path)
    return "Model updated"

def score(**contest):
    """Score companies using latest model."""
    ti = context["task_instance"]
    model_path = ti.xcom_pull(key='model_path', task_ids='updated_model')
    clean_path = ti.xcom_pull(key='clean_path', task_ids='preprocess')

    import joblib
    import pandas as pd
    model = joblib.load(model_path)
    df = pd.read_parquet(clean_path)

    hot_topic = find_hottest_topic(model, df, lookback_days=30)
    if hot_topic == -1:
        return "No hot topic found"
    
    recommendations = score_companies(model, df, hot_topic, our_company_name="YourCompany")
    out_csv = f"/data/output/recommendations_{context['ds'].csv"
    recommendations.to_csv(out_csv, index=False)
    # also saving to json for api
    recommendations.to_json("/api/data/latest_recommendations.json", orient='records')
    return "Scoring complete"

# define tasks
t1 = PythonOperator(task_id='fetch_news', python_callable=fetch_news, provide_context=True, dag=dag)
t2 = PythonOperator(task_id='fetch_reddit', python_callable=fetch_reddit, provide_context=True, dag=dag)
t3 = PythonOperator(task_id='preprocess', python_callable=preprocess, provide_context=True, dag=dag)
t4 = PythonOperator(task_id='update_model', python_callable=preprocess, provide_context=True, dag=dag)
t5 = PythonOperator(task_id='score', python_callable=score, provide_context=True, dag=dag)

[t1, t2] >> t3 >> t4 >> t5

















































    




























































    





