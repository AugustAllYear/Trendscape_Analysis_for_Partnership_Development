import os
import logging
import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from pythorhead import Lemmy

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.news_api_key = os.getenv("NEWSAPI_KEY", "")
        self.hacker_news_base = "https://hacker-news.firebaseio.com/v0"
        self.reddit_rss_urls = [
            "https://www.reddit.com/r/technology/.rss",
            "https://www.reddit.com/r/startups/.rss",
            "https://www.reddit.com/r/business/.rss"
        ]

    def fetch_hacker_news(self, limit=100):
        """Fetch top stories from Hacker News API (no API key required)"""
        try:
            # Get top stories IDs
            response = requests.get(f"{self.hacker_news_base}/topstories.json")
            top_ids = response.json()[:limit]
            
            stories = []
            for story_id in top_ids:
                story_response = requests.get(f"{self.hacker_news_base}/item/{story_id}.json")
                story = story_response.json()
                if story and story.get('type') == 'story':
                    stories.append({
                        'title': story.get('title', ''),
                        'content': story.get('text', '') or story.get('title', ''),
                        'source': 'Hacker News',
                        'published_at': datetime.fromtimestamp(story.get('time', 0)),
                        'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                    })
            logger.info(f"Fetched {len(stories)} Hacker News stories")
            return pd.DataFrame(stories)
        except Exception as e:
            logger.error(f"Error fetching Hacker News: {e}")
            return pd.DataFrame()

    def fetch_reddit_rss(self):
        """Fetch Reddit posts via RSS feeds (no API key required)"""
        articles = []
        for url in self.reddit_rss_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    articles.append({
                        'title': entry.get('title', ''),
                        'content': entry.get('summary', ''),
                        'source': 'Reddit RSS',
                        'published_at': datetime(*entry.get('published_parsed', [0]*6)[:6]),
                        'url': entry.get('link', '')
                    })
                logger.info(f"Fetched {len(feed.entries)} posts from {url}")
            except Exception as e:
                logger.error(f"Error fetching Reddit RSS from {url}: {e}")
        return pd.DataFrame(articles)

    def fetch_newsapi(self, query="technology", days_back=1):
        """Fetch news from NewsAPI.org (requires API key)"""
        if not self.news_api_key:
            logger.warning("NewsAPI key not set, skipping")
            return pd.DataFrame()
            
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'relevancy',
            'language': 'en',
            'pageSize': 100,
            'apiKey': self.news_api_key
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                df = pd.DataFrame([{
                    'title': a.get('title', ''),
                    'content': a.get('description', '') + ' ' + (a.get('content') or ''),
                    'source': a['source'].get('name', 'NewsAPI'),
                    'published_at': a.get('publishedAt'),
                    'url': a.get('url')
                } for a in articles])
                logger.info(f"Fetched {len(df)} news articles")
                return df
        except Exception as e:
            logger.error(f"Error fetching NewsAPI: {e}")
        return pd.DataFrame()

    def fetch_sauravkanchan_news(self, query="technology", limit=50):
        """Fetch news from SauravKanchan/NewsAPI (open source, no key)"""
        try:
            url = f"https://inshorts.deta.dev/news?category={query}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('data', [])[:limit]
                df = pd.DataFrame([{
                    'title': a.get('title', ''),
                    'content': a.get('content', ''),
                    'source': 'SauravKanchan News API',
                    'published_at': datetime.now(),
                    'url': a.get('url', '')
                } for a in articles])
                logger.info(f"Fetched {len(df)} news articles from SauravKanchan API")
                return df
        except Exception as e:
            logger.error(f"Error fetching SauravKanchan API: {e}")
        return pd.DataFrame()

    def fetch_lemmy_posts(self, community="technology", limit=50):
        """Fetch posts from Lemmy (decentralized Reddit alternative)"""
        try:
            lemmy = Lemmy("https://lemmy.dbzer0.com")
            # No login needed for reading public posts
            posts = lemmy.post.list(limit=limit, sort="Hot")
            if posts and 'posts' in posts:
                df = pd.DataFrame([{
                    'title': p.get('post', {}).get('name', ''),
                    'content': p.get('post', {}).get('body', ''),
                    'source': f'Lemmy (lemmy.dbzer0.com)',
                    'published_at': datetime.fromtimestamp(p.get('post', {}).get('published', 0)),
                    'url': p.get('post', {}).get('url', '')
                } for p in posts['posts']])
                logger.info(f"Fetched {len(df)} Lemmy posts")
                return df
        except Exception as e:
            logger.error(f"Error fetching Lemmy posts: {e}")
        return pd.DataFrame()
