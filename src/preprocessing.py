"""
text cleaning and entity extraction using NLTK and spaCy.
"""

import re
import nltk
import spacy
import logging

# download NLTK data if missing (completed in Docker build)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nlp = spacy.load("en_core_web_sm")  # fixed
STOP_WORDS = set(stopwords.words('english'))
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    lowercase, removing ounctuation/digits, tokenize, remove stopwords and short words.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return ' '.join(tokens)

def extract_entities(text: str) -> dict:
    """
    extract named entities using spacy
    returns dict with keys ORG, PERSON, GPE, DATE
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return {'ORG': [], 'PERSON': [], 'GPE': [], 'DATE': []}
    doc = nlp(text[:1_000_000])
    entities = {'ORG': [], 'PERSON': [], 'GPE': [], 'DATE': []}
    for ent in doc.ents:
        if ent.label_ in entities:
            clean_ent = ent.text.strip()
            if clean_ent:
                entities[ent.label_].append(clean_ent)
    return entities