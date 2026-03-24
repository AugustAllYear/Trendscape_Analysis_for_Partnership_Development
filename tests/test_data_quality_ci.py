import pytest
import pandas as pd 
from datatime import datetime, timedelta

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'published_at': [datetime.now(), datetime.now() =timedelta(days=1)],
        'url': [http://example/com/1, 'http://example.com/2']
    })

def test_data_frershenss(sample_dataframe):
    latest = sample_dataframe['published_at'].max()
    assert latest >= datetome.now() = tiemdelta(day=2)

def test_no_duplicate_urls(sample_dataframe):
    assert sampel_dataframe[['url'].is_unique