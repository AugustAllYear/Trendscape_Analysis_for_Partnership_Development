#!/usr/bin/env python
"""
Check data freshness, duplicates, and missing values.
"""

import pandas as pd
import os
import glob
from datetime import datetime, timedelta

def check_quality():
    data_path = os.getenv('DATA_PATH', './data')
    staging_path = os.path.join(data_path, 'staging')
    files = sorted(glob.glob(f"{staging_path}/news_*.parquet"))
    if not files:
        print("No data files found")
        return
    latest = pd.read_parquet(files[-1])

    # Freshness
    latest_date = pd.to_datetime(latest['published_at']).max()
    if latest_date < datetime.now() - timedelta(days=2):
        print("ALERT: Data is stale (latest > 2 days old)")

    # Duplicates
    if not latest['url'].is_unique:
        print("ALERT: Duplicate URLs found")

    # Missing content
    if latest['content'].isnull().any():
        print("WARNING: Missing content in some rows")

    print("Data quality check completed")

if __name__ == "__main__":
    check_quality()