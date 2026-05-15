import os
import time
import logging
import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

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

    def _retry(self, func, retries=3, delay=2):
        for i in range(retries):
            try:
                return func()
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                if i == retries - 1:
                    raise
                time.sleep(delay * (i+1))
        return None

    def fetch_hacker_news(self, limit=100):
        try:
            response = requests.get(f"{self.hacker_news_base}/topstories.json", timeout=10)
            top_ids = response.json()[:limit]
            stories = []
            for sid in top_ids:
                story_resp = requests.get(f"{self.hacker_news_base}/item/{sid}.json", timeout=10)
                story = story_resp.json()
                if story and story.get('type') == 'story':
                    stories.append({
                        'url': story.get('url', f"https://news.ycombinator.com/item?id={sid}"),
                        'title': story.get('title', ''),
                        'content': story.get('text', '') or story.get('title', ''),
                        'source': 'Hacker News',
                        'published_at': datetime.fromtimestamp(story.get('time', 0)),
                        'data_source': 'hacker_news'
                    })
            logger.info(f"Hacker News: {len(stories)} stories")
            return pd.DataFrame(stories)
        except Exception as e:
            logger.error(f"Hacker News failed: {e}")
            return pd.DataFrame()

    def fetch_reddit_rss(self):
        articles = []
        for url in self.reddit_rss_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    articles.append({
                        'url': entry.get('link', ''),
                        'title': entry.get('title', ''),
                        'content': entry.get('summary', ''),
                        'source': 'Reddit RSS',
                        'published_at': datetime(*entry.get('published_parsed', [0]*6)[:6]),
                        'data_source': 'reddit_rss'
                    })
                logger.info(f"Reddit RSS ({url}): {len(feed.entries)} entries")
            except Exception as e:
                logger.error(f"Reddit RSS failed for {url}: {e}")
        return pd.DataFrame(articles)

    def fetch_newsapi(self, query="technology", days_back=1):
        if not self.news_api_key:
            logger.warning("NewsAPI key missing, skipping")
            return pd.DataFrame()
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'relevancy',
            'language': 'en',
            'pageSize': 100,
            'apiKey': self.news_api_key
        }
        try:
            r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
            r.raise_for_status()
            articles = r.json().get('articles', [])
            df = pd.DataFrame([{
                'url': a.get('url', ''),
                'title': a.get('title', ''),
                'content': (a.get('description') or '') + ' ' + (a.get('content') or ''),
                'source': a['source'].get('name', 'NewsAPI'),
                'published_at': a.get('publishedAt'),
                'data_source': 'newsapi'
            } for a in articles])
            logger.info(f"NewsAPI: {len(df)} articles")
            return df
        except Exception as e:
            logger.error(f"NewsAPI failed: {e}")
            return pd.DataFrame()

    def fetch_sauravkanchan_news(self, query="technology", limit=50):
        try:
            url = f"https://inshorts.deta.dev/news?category={query}"
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json().get('data', [])[:limit]
            df = pd.DataFrame([{
                'url': a.get('url', ''),
                'title': a.get('title', ''),
                'content': a.get('content', ''),
                'source': 'SauravKanchan News API',
                'published_at': datetime.now(),
                'data_source': 'sauravkanchan'
            } for a in data])
            logger.info(f"SauravKanchan: {len(df)} articles")
            return df
        except Exception as e:
            logger.error(f"SauravKanchan failed: {e}")
            return pd.DataFrame()

    def fetch_lemmy_posts(self, instance="https://lemmy.dbzer0.com", limit=50):
        try:
            from pythorhead import Lemmy
            lemmy = Lemmy(instance)
            posts = lemmy.post.list(limit=limit, sort="Hot")
            if posts and 'posts' in posts:
                df = pd.DataFrame([{
                    'url': p.get('post', {}).get('url', ''),
                    'title': p.get('post', {}).get('name', ''),
                    'content': p.get('post', {}).get('body', ''),
                    'source': f'Lemmy ({instance})',
                    'published_at': datetime.fromtimestamp(p.get('post', {}).get('published', 0)),
                    'data_source': 'lemmy'
                } for p in posts['posts']])
                logger.info(f"Lemmy: {len(df)} posts")
                return df
        except Exception as e:
            logger.error(f"Lemmy failed: {e}")
        return pd.DataFrame()

    def fetch_all(self, limit_per_source=50):
        sources = [
            self.fetch_hacker_news,
            self.fetch_reddit_rss,
            lambda: self.fetch_newsapi(days_back=1),
            lambda: self.fetch_sauravkanchan_news(limit=limit_per_source),
            lambda: self.fetch_lemmy_posts(limit=limit_per_source)
        ]
        dfs = []
        for src in sources:
            df = src()
            if not df.empty:
                dfs.append(df)
        if not dfs:
            raise ValueError("No data fetched from any source")
        combined = pd.concat(dfs, ignore_index=True)
        combined['published_at'] = pd.to_datetime(combined['published_at'], errors='coerce')
        return combined
