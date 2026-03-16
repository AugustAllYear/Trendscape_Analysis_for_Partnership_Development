# Trendscape_Analysis_for_Partnership_Development

**Synopsis: Strategic opportunity mining via topic intelligence: implementation engaging News APIs, Schedule Pipelines and CI/CD**

Our goal is to identify emerging industry trends and potential cross industry partners for our client, media/technology company. In lieu of traditional research, to match the companies cutting edge interests an automated pipeline will best meet their business needs.

Factors that shaped the approch:
- Demand for timley content
- Identifying potentail collaborators who are gaining relevance
- Focus marketing spend twoards trending topics
- Daily monitoring to capture shifts quickly
- Early trend detection
- Enables agile marketing response 

The pipeline:
1. Ingests daily news and social media data
2. Detects trending topics using NPL
3. Identifies companies most associated with growth topics
4. Generates partnership recommendations for business development

### Technical Architecture:
- Data Sources: NewAPI.prd, Reddit API, Twitter API v2, SEC Edgar
- - The above sources are accessible with free tiers, high signal for technology and business trends, and of course legally gained.
- Processing: Apache Airflow DAG for orchestration, Spark for large-scale text processing
- NLP: spaCy = Transformers for entity extraction, BERTopic for dynamic topic modeling
- Storage: PostgreSQL for metadata, Elasticsearch for full-text search
- CI/CD: GitHub Actions + Docker + MLflow


# ADD TO README IN EXPLINATIONS!
3. Model, Storage, and CI/CD Decisions
Component	Choice	Rationale
Topic Modeling	BERTopic	State‑of‑the‑art, uses transformer embeddings, handles dynamic topics over time. Better than LDA for nuanced trends. LDA is a probabilistic model designed for topic discovery based on word frequency, whereas BERT is a deep learning model designed for contextual understanding and semantic representation
Entity Extraction	spaCy	Fast, accurate, pre‑trained for organization names.
Storage	PostgreSQL (metadata) + cloud blob (raw data)	PostgreSQL for querying, cloud storage (AWS S3 / GCS) for cost‑effective raw data retention.
CI/CD	GitHub Actions (free)	Integrates with code repository, can run tests and trigger model retraining on a schedule.
Why not Spark for everything?
While Spark is great for large‑scale batch processing, the data volume here (~a few hundred articles per day) is well within pandas’ capabilities. Spark would add unnecessary complexity.

4. Cost of Running This Model
Assuming you run daily on a small cloud VM (e.g., AWS t3.medium, $0.0416/hour ≈ $30/month):

Compute: $30–$50/month (including training once a week).

Storage: Negligible ($5/month for 50GB).

API costs: NewsAPI free tier (100 requests/day) – enough. Reddit API free. Total: $0.

CI/CD: GitHub Actions free tier (2000 min/month) – plenty.

Total estimated monthly cost: $35–$55 for a production‑grade pipeline. For a media tech company, this is trivial compared to the value of catching one good partnership early.