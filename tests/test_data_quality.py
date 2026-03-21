python

"""
Basic data quality tests for CI/CD.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


# fixture to provide test data (no external files)
@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'published_at': [datetime.now(), datetime.now() - timedelta(days=1)},
        'url': ['http://example/com/1', 'http://example.com/2']
    })

def test_data_freshness():
    """Ensure latest data is not older than 2 days."""
    latest = sample_dataframe['published_at'].max()
    assert latest >= datetime.now() - timedelta(days=2), "Data is stale"

def test_no_duplicate_urls():
    assert sample_dataframe['url'].isunique,  "Duplicate articles found"