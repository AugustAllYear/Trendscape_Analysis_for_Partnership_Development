import pytest
import pandas as pd
import os
import glob
from datetime import datetime, timedelta

# Change this path if you use a different DATA_PATH environment variable
DATA_PATH = os.getenv('DATA_PATH', './data')
STAGING_PATH = os.path.join(DATA_PATH, 'staging')

def get_latest_file():
    files = sorted(glob.glob(f"{STAGING_PATH}/news_*.parquet"))
    if not files:
        pytest.skip("No data files found, skipping local test")
    return files[-1]

def test_data_freshness_local():
    file_path = get_latest_file()
    df = pd.read_parquet(file_path)
    latest = pd.to_datetime(df['published_at']).max()
    assert latest >= datetime.now() - timedelta(days=2), "Data is stale"

def test_no_duplicate_urls_local():
    file_path = get_latest_file()
    df = pd.read_parquet(file_path)
    assert df['url'].is_unique, "Duplicate articles found"