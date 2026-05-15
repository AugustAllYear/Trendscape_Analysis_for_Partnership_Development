"""Unified database setup for Trendscape – used by DAG and SQL scripts."""
import sqlite3
import os

def get_db_path():
    """Return path to the main data database (not Airflow's metadata)."""
    return os.getenv("TRENDSCAPE_DB", "data/trendscape.db")

def create_unified_schema(conn):
    """Create the articles table and indexes for query optimization."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            article_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            source TEXT,
            published_at TIMESTAMP,
            data_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_data_source ON articles(data_source)")
    conn.commit()

def insert_articles_from_df(conn, df):
    """Insert articles from DataFrame, ignoring duplicates on url."""
    df[['url', 'title', 'content', 'source', 'published_at']].to_sql(
        "temp_articles", conn, if_exists="replace", index=False
    )
    conn.execute("""
        INSERT OR IGNORE INTO articles (url, title, content, source, published_at)
        SELECT url, title, content, source, published_at FROM temp_articles
    """)
    conn.execute("DROP TABLE temp_articles")
    conn.commit()
