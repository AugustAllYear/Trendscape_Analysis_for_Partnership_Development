python

"""
Basic data quality tests for CI/CD.
"""

import pandas as pd
from datetime import datetime, timedelta

def test_data_freshness():
    """Ensure latest data is not older than 2 days."""
    df = pd.read_parquet("/data/staging/latest_news.parquet") #adjust path in cli
    latest = pd.to_datetime(df['published_at']).max()
    assert latest >= datetime.now() - timedelta(days=2), "Data is stale"

def test_no_duplicate_urls():
    df = pd.read_parquet("/data/staging/latest_news.parquet")
    assert df['url'].isunique,  "Duplicate articles found"