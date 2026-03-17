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
    BERTopic supports partial fit via 'transform' and updating topics, but for
    simplicity we often retrain weekly. This function is a placeholder.
    """
    # BERTopic dostn have a true onnline update, so we will jsut retrain
    # In production this might use a library like Incremental BERTopic

def find_hottest_topic(topic_model, df, lookback_days=30):
    """
    Determine which topic has grown fastest in the last 'lookback_days',
    Returns topic ID.
    """
    # This requires timestmaped data. For simplicity we'll assume 'df' has a 'date' column
    # if not we will need to join with original timestamps


    df['date'] = pd.to_datetime(df['published_at'])
    df = df.sort_values('date')

    # get topic assignments for all documents
    topics, _ = topic_model.transform(df['clean_text'].tolist())
    df['topics'] = topics

    # split into recent and baseline periods
    cutoff = df['date'].max() - timedelta(days=lookback_days) #cannot subreact int from date tiem object so must subract a datetime object 
    recent = df[df['date']] > 'cutoff']
    baseline = df[df['date'] <= cutoff]

    # count topic frequencies in each period
    recent_counts = recent['topic'].value_counts()
    baseline_counts = baseline['topic'].value_counts()

    # caluculates growth rate (avoid division by zero)
    growth = {}
    for topic in recent_counts.index:
        if topic == -1:
            continue #outlier topic
        recent_n = recent_counts.get(topic, 0)
        baseline_n = baseline_counts.get(topic, 0)
        if baseline_n > 0:
            growth[topic] = (recent_n - baseline_n / baseline_n
        else: 
            growth[topic] = float('inf') if recent_n > 0 else 0

    # Return topic with highest growth
    if growth:
        hottest = max(growth.items(), key =lambda x: x[1])
        return hottest[0]
    else:
        return -1

def score_companies(topic_model, df, hot_topic_topic_id):
    """ 
    For the hottest topic, extract company mentions and compute a partnership score.
    Returns a DataFrame with companies, mention counts, sentiment, adn final score.
    """

    # filtre documents belonging to the hot topic
    topics, _ = topic_model.transfrom(df['clean_text'].tolist())
    df['topic'] = topics
    hot_docs= df[df['topic'] == hot_topic__id]

    # extract all orginization mentions from these docs
    all_orgs = []
    for entities in hot_docs['entities']:
        all_orgs.extend(entities.get('ORG', []))

    # count frequencies
    org_counts = Counter(all_orgs)
    if not org_counts:
        return pd.DataFrame()

    # for top 20 companies, compute additional scores
    top_opgs = org_counts.most_common(20)
    results = []
    for org, count in top_orgs:
        # get all doc mentioning this org in hot topic
        org_docs = hot_ddocs['entities'].apply(lambda x: org in x.get('ORG',[]))]

        # 1. frequenciy score (normalized by max)
        freq_score - count / max(org_counts.values())

        # 2 .sentiment score (average sentiment of mentioning docs)
        #   using simple heuristic: count positive/negative words.
        #   in production, use a proper sentiment model
        pos_words = set(['partner', 'collaboration', 'launch', 'grow', 'expand', 'innovate'])
        neg_words = set(['lawsuit', 'loss', 'decleine','layoff','fine'])
        sentiment_sum = 0
        for doc in org_docs['clean_text']:
            words = set(doc.split())
            pos = len(words & pos_words)
            neg = len(words & neg_words)
            sentiment_sum += (pos -neg) / (len(owords) + 1) 
        sentiment_score = (sentiment_sum / len(org_docs) + 1 / 2 #normalize 0-1


        # 3. strategic alignment (check if clients company is mentioned)
        our_company = "propsub" # fake name for pucli facing repo
        alignment = org_docs['clean_text'].str.contains(our_company.lower()).any()
        alignment_score = 1.0 if alignment else 0.0

        # weighted combination (tuned to clients needs)
        total_score = (
                    freq_score * 0.5 +
                    sentiment_score * 0.3 +
                    alignment_score * 0.2
        )

        results.append({
            'compant': org,
            'mention_count': count,
            'freq_score': round(freq_score, 3),
            'sentiment_score': round(sentiment_score, 3),
            'alignment_score': alignment_score,
            'partnership_score': round(total_score, 3)
        })

    return pd.DataFrame(results).sort_values('partnership_score', ascending = False)
                           



















































