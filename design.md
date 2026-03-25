# Design Document

## 1. Overview

This project delivers a production-ready data pipeline that ingests daily news and social media content, identifies emerging buisness trends using state-of-the-art NLP (BERTopic), and generates actionable partnership recommendations for a media technology company.

The system is designed to:
- Detect trending topics before they become mainstream.
- Identify companies most frequently associated with these topics.
- Score each company's partnership potential using frequency, sentiment and strategic alignment.

## 2. Architectural Decisions

The following choices were made to balance performance, maintainability, and cost.

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Topic Modeling** | BERTopic | Transformer‑based; captures contextual meaning and dynamic topics. Outperforms LDA on nuanced, real‑world text. |
| **Entity Extraction** | spaCy | Fast, pre‑trained for organization names; integrates easily with Python. |
| **Storage** | PostgreSQL (metadata) + cloud blob (raw) | PostgreSQL for queryable metadata; cloud storage (S3/GCS) for cost‑effective retention of raw data. |
| **Orchestration** | Apache Airflow | Industry standard for scheduling and monitoring data pipelines. |
| **CI/CD** | GitHub Actions | Free tier, integrates directly with code repository; runs tests and model training on schedule. |
| **Processing Scale** | pandas | Data volume (~hundreds of documents/day) fits comfortably in pandas; Spark would add unnecessary overhead. |

### 2.1 High-Level Data Flow
## 2.1 High‑Level Data Flow

The pipeline follows a sequential, daily‑batch process:

### Data Ingestion
- Airflow triggers two parallel tasks: one fetches news articles via NewsAPI, another fetches Reddit posts via PRAW.
- Raw data is stored as Parquet files in a staging directory (`./data/staging/`).

### Preprocessing
- Text is cleaned (lowercase, punctuation removed, tokenized, stopwords removed) using NLTK.
- Named entities (organizations, people, locations) are extracted using spaCy.
- Cleaned text and entities are saved as Parquet in a processed directory (`./data/processed/`).

### Topic Modeling
- A BERTopic model is trained (or updated) on the last 90 days of clean text.
- The model assigns each document to a topic and calculates topic probabilities.
- The trained model is saved to `./models/latest_topic_model.pkl`.

### Trend Detection
- Topic growth rates are computed by comparing the frequency of each topic in the last 30 days to the previous 30‑day baseline.
- The fastest‑growing topic is identified as the “hottest” trend.

### Company Scoring
- Within the hottest topic, organizations mentioned in the text are counted.
- For each organization, a partnership score is calculated using:
  - **Mention frequency** (normalized)
  - **Sentiment score** (via a transformer‑based sentiment model)
  - **Strategic alignment** (whether our company is mentioned alongside)
- The top companies and their scores are saved as CSV and JSON (`./data/output/` and `./api/data/`).

### API & Dashboard
- The FastAPI service serves the latest recommendations and model metrics.
- A Streamlit dashboard provides an interactive view of the data.

### Data Flow Diagram (simplified)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ NewsAPI         │────▶│                 │     │                 │
│ Reddit          │────▶│  Airflow DAG    │────▶│  Parquet Store  │
└─────────────────┘     │  (daily)        │     │  (raw + proc)   │
                        └─────────────────┘     └─────────────────┘
                                 │                       │
                                 ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  BERTopic       │◀────│  Preprocessing  │
                        │  (topic model)  │     │  (NLTK, spaCy)  │
                        └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Scoring        │
                        │  (frequency,    │
                        │   sentiment,    │
                        │   alignment)    │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  FastAPI        │────▶  Recommendations
                        │  + Streamlit    │          (JSON/CSV)
                        └─────────────────┘
```
### 2.2 Component Details

### 2.2 Component Details

| Component               | Technology                         | Purpose                                                                 |
|-------------------------|------------------------------------|-------------------------------------------------------------------------|
| Data Ingestion          | NewsAPI, PRAW (Reddit)             | Fetches articles and posts daily.                                      |
| Orchestration           | Apache Airflow 2.7.3               | Schedules daily DAG; handles retries and failure alerts.               |
| Storage                 | Parquet (local / cloud)            | Stores raw and processed data efficiently.                             |
| Topic Modeling          | BERTopic + SentenceTransformers    | Generates dynamic topics from text; captures semantic meaning.         |
| Entity Extraction       | spaCy                               | Identifies organization names from text.                               |
| Sentiment Analysis      | Hugging Face Transformers          | Provides sentiment scores for mentions.                                 |
| Scoring                 | Custom Python (pandas)             | Combines frequency, sentiment, alignment into partnership score.       |
| API                     | FastAPI                            | Serves recommendations and model metrics.                              |
| Dashboard               | Streamlit + Plotly                 | Visualizes top recommendations and model health.                       |
| CI/CD                   | GitHub Actions                     | Tests, trains, and deploys on push/schedule.                           |
| Containerization        | Docker                             | Ensures reproducibility and ease of deployment.                        |

## 3. Data Sources

| Source          | Data Type               | Frequency | API Limits               | Notes                                   |
|-----------------|-------------------------|-----------|--------------------------|-----------------------------------------|
| NewsAPI         | Articles (title, content)| Daily     | 100 requests/day (free)  | Focus on technology, business, startup. |
| Reddit (PRAW)   | Posts (title, selftext) | Daily     | 60 requests/min (free)   | Subreddits: technology, startups, business. |

All data is stored in Parquet format for compression and fast I/O. A rolling 90‑day window is kept for topic modeling.

## 4. Model Evaluation Metrics

### 4.1 Topic Model Quality

- **Number of Topics**: Automatically determined by BERTopic; we expect 5–20 interpretable topics.
- **Outlier Ratio**: Documents assigned to topic `-1` (no clear topic) should remain below 20%.
- **Coherence (c_v)**: Measures how semantically similar the top words of a topic are. Target > 0.5 (on a 0–1 scale).
- **Stability**: Topic distributions should not change drastically week‑over‑week; we monitor Jensen‑Shannon divergence.

### 4.2 Partnership Scoring

- **Frequency Score**: Normalized mention count in the hottest topic.
- **Sentiment Score**: Average of transformer‑based sentiment (0–1) for all documents mentioning the company.
- **Alignment Score**: Binary indicator of whether our own company appears in the same document (indicates existing relationship).
- **Final Score**: Weighted sum (50% frequency, 30% sentiment, 20% alignment).

These weights were chosen through stakeholder interviews to prioritize high‑volume mentions (frequency) while rewarding positive sentiment and existing connections.

## 5. Infrastructure Decisions

| Area               | Decision                     | Rationale                                                                 |
|--------------------|------------------------------|---------------------------------------------------------------------------|
| Processing Scale   | pandas                       | Daily data volume (<1000 docs) fits comfortably; Spark would be overkill. |
| Storage            | Parquet + optional cloud     | Parquet for performance; cloud storage if long‑term retention needed.    |
| Orchestration      | Airflow                      | Industry standard, easy to schedule and monitor.                         |
| CI/CD              | GitHub Actions               | Free tier, integrates with repo, can run tests and training.             |
| Deployment         | Docker + FastAPI             | Portable; API can be scaled horizontally if needed.                      |

## 6. Expected Outcomes (6‑Month Forecast)

Based on historical simulations and industry benchmarks for a mid‑sized media tech company:

- **Partnership Revenue**: $15,000–$25,000 from new sponsorships.
- **Audience Growth**: 30% increase in newsletter subscribers (+5,000–8,000 users).
- **Marketing Efficiency**: 22% lift in social engagement, 18% lower CPC.
- **Strategic Advantage**: Time to identify potential partners reduced from weeks to hours.

### 6.1 Cost Estimation (Monthly)

These estimates are realistic for a small-scale production deployment on a single t#.medium instance (or equivalent) with 50 GB of storage. The copute cost may vary by region and provider, but it's a reasonable ballpark. The GitHub Actions free tier is sufficient for this pipeline (2000 minutes/month).

Resource	Estimated Cost
Compute (t3.medium)	$30
Storage (50 GB)	$5
API Fees (free tiers)	$0
GitHub Actions (free)	$0
Total	$35–$50

## 7. Future Improvements

- **Real‑time streaming**: Replace daily batch with Kafka for near‑real‑time detection.
- **Fine‑tuned sentiment**: Use a domain‑specific model (e.g., finance/business).
- **Feedback loop**: Store user‑marked successful partnerships and use them to retrain scoring weights.
- **Interactive dashboard**: Add historical trend graphs and drill‑down by topic.

## 8. Other Use Case Examples

The core pipeline (daily data ingestion -> entity extraction -> scoring) is highly adaptable. Other use cases for a similair modeling approach:

- Competitive Intelligence - Monitor news about copetitors, track their product launches, funding, partnerships scores, outpput competitor threat levels.
- Brand Monitoring - Track mentions of your own brand across news and social media, measue sentiment, and identicy influencers who mention you.
- Crisis Detection - Look for sudden spikes in negative sentiment or specific keywords (e.g., "recall", "lawsuits") to alret PR teams.
- Trend-Driven Content Creation - Use trending topics to suggest blog post ideas, video topics, or ad copy for marketing teams.
- Investment Research - For a VC firm track emergin startups in specific sectors and score them based on media buzz and funding news.

With slight adjusments to scoring logic and the output format (e.g., a dashboard, alerts, or a weekly report.)

## 9. References

- BERTopic documentation: https://maartengr.github.io/BERTopic/
- NewsAPI: https://newsapi.org/
- Reddit API (PRAW): https://praw.readthedocs.io/
- spaCy: https://spacy.io/
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://streamlit.io/