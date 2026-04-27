"""
functions to fetch data from external APIs and create tables
"""
import pandas as pd
import logging
import os
import praw 
import requests
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def fetch_news_api(api_key: str, days_back: int = 1) -> pd.DataFrame:
    """ 
    fetch news article from NewsAPI.org for the last 'days_back' days.
    """
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    url = "https://newsapi.org/v2/everything"  # fixed to https
    params = {
        'q': 'technology OR business OR startup',
        'from': from_date,
        'sortBy': 'relevancy',
        'language': 'en',
        'pageSize': 100,
        'apiKey': api_key
    }
    logger.info(f"Fetching news from {from_date}")
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        logger.error(f"NewsAPI error: {resp.text}")
        return pd.DataFrame()

    articles = resp.json().get('articles', [])
    data = []
    for art in articles:
        data.append({
            'title': art.get('title', ''),
            'content': art.get('description', '') + ' ' + (art.get('content') or ''),
            'source': art['source'].get('name', 'unknown'),
            'published_at': art.get('publishedAt'),
            'url': art.get('url'),
        })
    df = pd.DataFrame(data)
    logger.info(f"Fetched {len(df)} news articles")
    return df

def fetch_reddit_posts(client_id: str, client_secret: str,
                       subreddits: list, limit: int = 50) -> pd.DataFrame:
    """
    Fetch top posts from given subreddits using Reddit API (PRAW).
    """
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent='MarketIntelligenceBot/1.0'
    )
    posts = []
    for subr in subreddits:
        subreddit = reddit.subreddit(subr)
        for post in subreddit.hot(limit=limit):
            posts.append({
                'title': post.title,
                'content': post.selftext,
                'source': f"reddit/{subr}",
                'published_at': datetime.fromtimestamp(post.created_utc),
                'url': f"https://reddit.com{post.permalink}",
                'score': post.score,
                'num_comments': post.num_comments
            })
    df = pd.DataFrame(posts)
    logger.info(f"Fetched {len(df)} Reddit posts")
    return df


DB_PATH = os.getenv("TRENDSCAPE_DB", "data/trendscape.db")

def create_tables(conn):
    """Create tables for articles, companies, and the junction table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            article_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            source TEXT,
            published_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_companies (
            article_id INTEGER,
            company_id INTEGER,
            FOREIGN KEY(article_id) REFERENCES articles(article_id),
            FOREIGN KEY(company_id) REFERENCES companies(company_id)
        )
    """)
    conn.commit()

def insert_articles(conn, df):
    """Insert or ignore articles into SQLite."""
    # Use a temporary in‑memory table to avoid duplicates
    df.to_sql("temp_articles", conn, if_exists="replace", index=False)
    conn.execute("""
        INSERT OR IGNORE INTO articles (url, title, content, source, published_at)
        SELECT url, title, content, source, published_at FROM temp_articles
    """)
    conn.execute("DROP TABLE temp_articles")
    conn.commit()