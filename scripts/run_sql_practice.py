"""Run SQL queries to test query optimization adn measure performance."""

import sqlite3
import time
from src.data_fetchers import DB_PATH
from src.sql_queries import deduplicate_articles, monthly_article_counts, get_company_mentions, create_indexes

def track_time(func, conn, name):
    start = time.time()
    df = func(conn)
    elapsed = time.time() - start
    print(f"{name}: {len(df)} rows, took {elapsed:.3f} seconds")
    return df

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    # Ensure indexes are there (for runtime comparison)
    create_indexes(conn)

    # Run queries
    dedup_df = track_time(deduplicate_articles, conn, "Deduplication")
    monthly_df = track_time(monthly_article_counts, conn, "Monthly counts")
    mentions_df = track_time(get_company_mentions, conn, "Company mentions")

    # Demonstrate before/after indexing (optional)
    print("\nTo see index impact, drop an index and re‑run the query.")
    conn.close()