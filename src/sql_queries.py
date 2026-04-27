"""SQL queries for metadata analysis and optimization examples."""

import sqlite3
import pandas as pd


# 1. Deduplicate articles per URL using a window function

DEDUP_QUERY = """
WITH ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY url ORDER BY published_at DESC) AS rn
    FROM articles
)
SELECT * FROM ranked WHERE rn = 1;
"""

def deduplicate_articles(conn):
    """Run the deduplication query and return a DataFrame with unique articles."""
    return pd.read_sql_query(DEDUP_QUERY, conn)


# 2. Monthly article count per source (time‑based aggregation)

MONTHLY_COUNT_QUERY = """
SELECT
    strftime('%Y-%m', published_at) AS month,
    source,
    COUNT(*) AS article_count
FROM articles
WHERE published_at >= date('now', '-6 months')
GROUP BY month, source
ORDER BY month DESC, article_count DESC;
"""

def monthly_article_counts(conn):
    return pd.read_sql_query(MONTHLY_COUNT_QUERY, conn)


# 3. Join with companies table to count mentions per company per month

COMPANY_MENTIONS_QUERY = """
WITH company_mentions AS (
    SELECT
        a.article_id,
        c.company_name,
        strftime('%Y-%m', a.published_at) AS month
    FROM articles a
    JOIN article_companies ac ON a.article_id = ac.article_id
    JOIN companies c ON ac.company_id = c.company_id
)
SELECT
    month,
    company_name,
    COUNT(*) AS mention_count,
    ROW_NUMBER() OVER (PARTITION BY month ORDER BY COUNT(*) DESC) AS rank
FROM company_mentions
GROUP BY month, company_name
ORDER BY month DESC, mention_count DESC;
"""

def get_company_mentions(conn):
    return pd.read_sql_query(COMPANY_MENTIONS_QUERY, conn)


# 4. Create indexes (run once after table creation)

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);",
    "CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);",
    "CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);",
    "CREATE INDEX IF NOT EXISTS idx_article_companies_article ON article_companies(article_id);",
]

def create_indexes(conn):
    for idx_sql in CREATE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()