import feedparser
from bs4 import BeautifulSoup
import requests

def fetch_rss_feed(url):
    """Generic RSS feed fetcher"""
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            articles.append({
                'title': entry.get('title', ''),
                'content': entry.get('summary', ''),
                'source': 'RSS Feed',
                'published_at': datetime(*entry.get('published_parsed', [0]*6)[:6]),
                'url': entry.get('link', '')
            })
        return articles
    except Exception as e:
        logger.error(f"Error fetching RSS feed {url}: {e}")
        return []


