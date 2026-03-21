"""
functions to fetch data from external APIs
"""

import pandas as pd
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def fetch_news_api(api_key: str, days_back: int=1) -> pd.DataFrame:
    """ fetch news article from NewsAPI.org for the last 'days_back' days."""
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    url = "http://newsapi.org/v2/everything"
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
    import praw
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










    