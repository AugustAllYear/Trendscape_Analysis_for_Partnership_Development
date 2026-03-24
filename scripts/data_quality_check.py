import pandas as pd
impor os
import glob
from datetime import datetime, timedelta

def check_data_quality():
    data_path = os.getenv('DATA_PATH', './data/staging')
    files = sorted(glob.glob(f"{data_path}/news_*.parquet")
    if not files: 
        print("No data files found")
        return
    latest = pd.read_parquet(files[-1])
    # freshness
    latest_date = pd.to_datetime(latest['published_at']).max()
    if latest_date < datetime.now() - timedelta(days=2):
        print("Alert: Data is stale (latest > 2 days old)")
    # duplicates
    if not latest['url'].is_unique:
        print("Alert: Duplicate URLS found")
    # misisng values
    if latest['content'].isnull().any():
        print("Warning: Misssing content in somem rows")
    print("Data quality check completed")

if __name__ == "__main__":
    check_quality()