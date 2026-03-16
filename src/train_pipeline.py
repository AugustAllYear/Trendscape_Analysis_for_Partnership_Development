""" 
Core traininf pipeline for market intelligence.
All functions are designed to be used in Airflow tasks.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import requests
import re
import nltk 
import spacy
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from collections import COunter
import joblib
import os


#  confihire loggong
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  download NLTK
try: 
    nltk.data.find('tokenizers/ounkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenizer import work_tokenize

# load spacy model for entity recognition
#  (run once: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

STOP_WORDS = set(stopwords.words('english'))

def fetch_news_api(api_key, days_back=1):
    """
    Fetch news articles from NewsAPI.org for the last 'days_back' days.
    Returns a DataFrame with columns: title, content, source, published_at, url.
    """
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    url = 'https://newsapi.org/v2/everything"
    params = {
        'q': 'technology OR business OR startup', # broad query
        'from': from_date,
        'sortBy': 'relevancy',
        'language': 'en',
        'pageSize': 100,
        'apiKey': api_key
    }
    logger.info(f"Fetuching news from {from_date}")
    response = requests.get(url, params=params)
    if response.status_code != 200:
        logger.error(f"NewsAPI error: {response.text}")
        return pd.DataFrame()

    articles = response.json().get('articles', [])
    data = []
    for art in articles:
        data.append({
            'title': art.get('title', ''),
            'content': art.get('description', '') + ' ' + (artr.get('content', '') or ''),
            'source': art['source'].get('name', 'unknown'),
            'published_at': art.get('publishedAt'),
            'url':art.get('url'),
        })
    df = pr.DataFrame(data)
    logger.info(f"Fetched {len(df)} news articles")
    return df

def fetch_reddit_posts(client_id, client_secret, subreddits, limit=50):
    """
    Fetch top posts form given subreddits using Reddit API (PRAW).
    Returns a DataFrame with title, content, source, created_utc.
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
            post.append({
                'title':post.title,
                'content':post.sefltext,
                'source':f"reddit/{subr}",
                'published_at': datetime.fromtimestamp(post.created_utc),
                'url': f"https://reddit.com(post.permalink}",
                'score':post.score,
                'num_somments': post.num_comments
            })
    
    df = pd.DataFrame(posts)
    logger.info(f"Fetched {len(df)} Reddit posts")
    return df
    
def clean_text(text):
    """
    Basic test cleaning
    - Lowercase
    - Remove punctuation and digits
    - Tokenize
    - Remove stopwords and short words
    """

    if not isinstance(text, str):
        return ""
        # lowercase
        text = text.lower()
        # remove puncuation and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text
        # tokenize
        tokens = word_tokenize(text)
        #  remove stopwords and words shorter than 3 chars
        tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
        return ' '.join(tokens)

def extract_entites(text):
    """
    Use spaCy to extract named entities, focusing on organizations.
    Returns a dictionary or entity types -> list of entity texts.
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return {'ORG'" [], 'PERSON': [], 'GOE': [], 'DATE': []}
    doc = nlp(text[:1_000_000]) # limit to 1m chars for performance
    entities = {'ORG': [], 'PERSON': [], 'GPE': [], 'DATE': []}
    for ent in doc.ents:
        if ent.label_ in entities:
            # clean entity text (remove trailing spaces, ect.)
            clean_ent = ent.text.strip()
            if clean_ent:
                entities[ent.label_]append(clean_ent)
    return entities

def train_topic_model(texts, min_topic_size=10):
    """
    Train a BERTopic model on a lsit of texts.
    Returns (topic_model, topics, probabilites).
    """
    logger.info(f"Training BERTopic on {len(texts)} documents")
    # use a small sentence transformer for speed
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    topic_model = BERTopic(
        embedding_model=embedding_model,
        min_topic_size=min_topic_size,
        verbose=True,
        calculate_probabilites=True,
    )
    topics, probs = topic_model.fit_transform(texts)
    logger.info(f"Found {len(set(topics)) - (1 if -1 in topics else 0)} topics")
    return topic_model, topics, probs

def update_topic_model(topic_model, new_texts):
    """
    Update an excisting BERTopic model with new texts (incremental learning).
    
        






























































