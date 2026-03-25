""" 
Partnership scoring logic using transformer-based sentiment analysis.
"""
import pandas as pd
import numpy as np
from collections import Counter
from transformers import pipeline
import logging

# configure logger
logger = logging.getLogger(__name__)

# load sentiment model once at module level
_sentiment_pipeline = None

def get_sentiment_pipeline():
    """ lazy loading to not load at import time."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Loading sentiment model (distilbert-base-uncased-finetuned-sst-2-english)")
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1
        )
    return _sentiment_pipeline

def get_sentiment_score(text: str) -> float:
    """
    Return a sentiment score between 0 (negativ and 1 (positive)
    """
    if not isinstance(text, str) or len(text.strip()) < 10:
        return 0.5
    pipe = get_sentiment_pipeline()
    result = pipe(text[:512])[0]
    label = result['label']
    score = result['score']
    if label == 'POSITIVE':
        return score
    elif label == 'NEGATIVE':
        return 1 - score
    else:
        return 0.5

def score_companies(topic_model, df, hot_topic_id, our_company_name: str = "YourCompany"): 
    """
    For hosttest topic, extract company mentions and compute a partnership score.
    Returns a DataFrame with compaies, mention counts and scores.
    """
    #  filter documents belonging to hot topic
    topics, _ = topic_model.transform(df['clean_text'].tolist())
    df = df.copy()
    df['topic'] = topics
    hot_docs = df[df['topic'] == hot_topic_id]

    if len(hot_docs) == 0:
        return pd.DataFrame()

    # extract all orginization mentions from these docs
    all_orgs = []
    for entities in hot_docs['entities']:
        all_orgs.extend(entities.get('ORG', []))

    org_counts = Counter(all_orgs)
    if not org_counts:
        return pd.DataFrame()

    top_orgs = org_counts.most_common(50)
    max_count = max(org_counts.values())

    results = []
    for org, count in top_orgs:
        # get all docs mentioning this org in hot topic
        org_docs = hot_docs[hot_docs['entities'].apply(lambda x: org in x.get('ORG', []))]
        # 1. frequency score (normalized)
        freq_score = count / max_count
        # 2. sentiment socre (average of all docs mentioning this company
        sentiments = [get_sentiment_score(doc) for doc in org_docs['clean_text']]
        sentiment_score = np.mean(sentiments) if sentiments else 0.5
        # 3. strategic alignment: is our company mentioned in the sae doc
        our_mentioned = org_docs['clean_text'].str.contains(our_company_name.lower()).any()
        alignment_score = 1.0 if our_mentioned else 0.0
        # weighted combination (tune weight with stakeholders)
        total_score = (freq_score * 0.5 + sentiment_score * 0.3 + alignment_score * 0.2)
        results.append({
            'company': org,
            'mention_count': count,
            'freq_score': round(freq_score, 3),
            'sentiment_score': round(sentiment_score, 3),
            'alignment_score': alignment_score,
            'partnership_score': round(total_score, 3)
        })

    return pd.DataFrame(results).sort_values('partnership_score', ascending=False)