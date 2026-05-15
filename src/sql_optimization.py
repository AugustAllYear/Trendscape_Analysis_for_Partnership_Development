import time
import sqlite3
import pandas as pd
from src.db_setup import get_db_path

def benchmark_query_performance(db_path=None):
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    queries = {
        'Window Functions Dedup': '''
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY source ORDER BY published_at DESC) AS rn
                FROM articles
            )
            SELECT * FROM ranked WHERE rn = 1
        ''',
        'Time Range Query': '''
            SELECT COUNT(*) FROM articles
            WHERE published_at > datetime('now', '-7 days')
            GROUP BY source
        ''',
        'Source Aggregation': '''
            SELECT source, COUNT(*) as cnt, AVG(LENGTH(content)) as avg_len
            FROM articles
            GROUP BY source
            ORDER BY cnt DESC
        ''',
        'Complex Join': '''
            SELECT a.source, a.published_at, a.title
            FROM articles a
            WHERE a.published_at > datetime('now', '-30 days')
            ORDER BY a.published_at DESC
            LIMIT 100
        '''
    }
    results = {}
    for name, sql in queries.items():
        start = time.time()
        df = pd.read_sql_query(sql, conn)
        elapsed = time.time() - start
        results[name] = {'rows': len(df), 'time': elapsed}
    conn.close()
    return results

if __name__ == "__main__":
    import json
    res = benchmark_query_performance()
    print(json.dumps(res, indent=2))
