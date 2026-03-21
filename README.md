# Trendscape_Analysis_for_Partnership_Development

**Synopsis: Strategic opportunity mining via topic intelligence: implementation engaging News APIs, Schedule Pipelines and CI/CD**

Our goal is to identify emerging industry trends and potential cross industry partners for our client, media/technology company. In lieu of traditional research, to match the companies cutting edge interests an automated pipeline will best meet their business needs.

The deliverable is a production-ready data pipeline that ingests news and social media daily, detects emerging business trends using state-of-the-art NLP (BERTopic), and generates partnership recommendations for media and technology companies

Factors that shaped the approach:
- Demand for timely content
- Identifying potential collaborators who are gaining relevance
- Focus marketing spend towards trending topics
- Daily monitoring to capture shifts quickly
- Early trend detection
- Enables agile marketing response 

## Features

- **Daily data ingestions** from NewsAPI and Reddit.
- **Automated text preprocessing.** (NLTK, spaCy).
- **Dynamic topic modeling** with BERTopic (transformer-based).
- **Entity extraction** to identify companies mentioned in trending topics.
- **Partnership scoring** using mention frequency, transformer sentiment, and strategic alignment.
- **FastSPI services** to deliver recommendations to business teams,.
- **Orchestration** with Apache Airflow.
- **CI/CD** with GitHub Actions + MLflow tracking.
- **Containerized** with Docker for easy deployment.

## Technology Stack

| Component          | Technology                         |
|--------------------|------------------------------------|
| Orchestration      | Apache Airflow 2.7.3               |
| Data Processing    | Python 3.11, pandas, numpy         |
| NLP                | BERTopic, spaCy, NLTK, transformers|
| Machine Learning   | scikit-learn, MLflow                |
| API                | FastAPI, Uvicorn                    |
| Database           | PostgreSQL (metadata), Parquet files|
| CI/CD              | GitHub Actions, Docker              |


### File Structure

```

Trendscape_Analysis_for_Partnership_Development/
├── dags/                           # Airflow DAGs
│   └── market_intelligence_dag.py
├── src/                            # Core Python modules
│   ├── data_fetchers.py            # API calls
│   ├── preprocessing.py            # Text cleaning, NER
│   ├── topic_model.py              # BERTopic training, trend detection
│   └── scoring.py                  # Partnership scoring (with sentiment)
├── api/                            # FastAPI service
│   └── main.py
├── tests/                          # Unit tests
│   └── test_data_quality.py
├── .github/workflows/              # CI/CD
│   └── market_intelligence.yml
├── requirements.txt
├── Dockerfile
└── README.md

```

## Architectural Decisions

The following choices were made to balance performance, maintainability, and cost.

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Topic Modeling** | BERTopic | Transformer‑based; captures contextual meaning and dynamic topics. Outperforms LDA on nuanced, real‑world text. |
| **Entity Extraction** | spaCy | Fast, pre‑trained for organization names; integrates easily with Python. |
| **Storage** | PostgreSQL (metadata) + cloud blob (raw) | PostgreSQL for queryable metadata; cloud storage (S3/GCS) for cost‑effective retention of raw data. |
| **Orchestration** | Apache Airflow | Industry standard for scheduling and monitoring data pipelines. |
| **CI/CD** | GitHub Actions | Free tier, integrates directly with code repository; runs tests and model training on schedule. |
| **Processing Scale** | pandas | Data volume (~hundreds of documents/day) fits comfortably in pandas; Spark would add unnecessary overhead. |

## Getting Started 

### Prerequisites

- Python 3.11
- Apache Spark 3.5.8
- Java 11 or 17 (if using SPark)
- Docker (options)

### Installation

1. Clone the repository:
   bash

```
   git clone https://github.com/AugustAllYear/Trendscape_Analysis_for_Partnership_Development.git
   cd Trendscape_Analysis_for_Partnership_Development.git
```
   
3. Create and activate a virtual environment:

   bash
   
```
   python3.11 -m venv vevn --prompt trendscape
   source venv/bin/activate  #Linux/macOS
   # .\venv\Scripts\activate  # Windows
```
   
5. Install dependencies:

```
    pip install --upgrade pip
    pip install -r requirements.txt
```
    
6. Download requiremed NLP models (this will be doen automatically on the first run, but you can pre-downlaod):

   bash
   
```
   python -m spacy download en_core_web_sm
   python -m nltk.downloader stopwords punkt
```
   
7. Set up environment variables (create a .env file or export):

   bash

```
   export AIRFLOW_HOME=$(pwd)/airflow
   export NEWSAPI_KEY=""
   export REDDIT_CLIENT_ID=""
   export REDDIT_CLIENT_SECRET=""
```

**Obtaining API keys:**
- NewsAPI: Register at newsapi.org for a free API key.
- Reddit API:
  1. Go to reddit.com/prefs/apps
  2. click "create app" and choose "script".
  3. fill in name, description, and redirect URI (e.g., http://localhost:8000).
  4. After creation, note the client_id (under the app name) and client_secret.

6. Initialize Airflow:

   bash

```
   airflow db init
   airflow users create \
   --username create \
   --firstname Admin \
   --lastname User \
   --role Admin \
   --email admin@example.com \
   --password admin
```
   
### Running Locally 

1. Start an Airflow scheduler and webserver (inseperate terminals):

   bash

```
   airflow schedules
   #in another terminal
   airflow webserver --port 8080
```

   Access the UI at http://localhost:8080


3. Trigger the DAG manually or wait for the schedules run.

4. Start the FASTAPI service:

    bash

```
    uvicorn api.main:app --reload --port 8000
```
    
API documentation available at http://localhost:8000/docs

### Running with Docker
Build the image:

    bash

```
    docker build -t trendscape .
    
```

Run the container:

    bash
```
    docker run -p 8000:8000 -p 8080:8080 \
    -e NEWSAPI_KEY=your_key\
    -e REDDIT CLIENT ID=your id \
    -e REDDIT_CLIENT_SECRET=your_secret \
    trendscape
```

### CI/CD Pipeline

the GitHub Actions workflow (.github/workflows/market_intelligence.yml) runs:
- On every push to main and daily at 3 AM.
- installs dependencies and runs data quality test.
- Trains the topic model on recent data.
- Logs metrics to MLflow.
- (Optional) Deploys the API is test pass.

### View Results (FastAPI endpoint)


### Cost Estimation (Monthly)
Resource	Estimated Cost
Compute (t3.medium)	$30
Storage (50 GB)	$5
API Fees (free tiers)	$0
GitHub Actions (free)	$0
Total	$35–$50


### Airflow Import Errors
Ensure your virtual environment is activated and AIRFLOW_HOME is set correctly. Use the constraints file if dependency conflicts arise.

## License
See LICENSE

## Contact
For questions, contact the augustvollbrecht@proton.me.

## Future Development & Next Steps

- **Add real-time streaming** - Intergrate with a message queue (e.g., Kafka) to process incoming articles as they are published.
- **Improve sentiment analysis** - Fine-tune a transformer model on company-cpecific datya for more accurate sentiment scoring.
- **Deploy to cloud** - COntainerize the pipeline and deploy on AWS/GCP with managed Airflow (e.g., MWAA, Cloud Composer).
- **Add a feedback loop** - Allow business users to mark recommendations as successful; use that to retrain the scoring model.
- **Build a dashboard**- Create an interactive dashboard (Stremlit or Tableau) that displays treanding topics and partner scores in real time.
- **Monitor model drift** - Set up automated alerts when topic distributions change significantly. 

## Other Use Case Examples

The core pipeline (daily data ingestion -> entity extraction -> scoring) is highly adaptable. Other use cases for a similair modeling approach:

- Competitive Intelligence - Monitor news about copetitors, track their product launches, funding, partnerships scores, outpput competitor threat levels.
- Brand Monitoring - Track mentions of your own brand across news and social media, measue sentiment, and identicy influencers who mention you.
- Crisis Detection - Look for sudden spikes in negative sentiment or specific keywords (e.g., "recall", "lawsuits") to alret PR teams.
- Trend-Driven Content Creation - Use trending topics to suggest blog post ideas, video topics, or ad copy for marketing teams.
- Investment Research - For a VC firm track emergin startups in specific sectors and score them based on media buzz and funding news.

With slight adjusments to scoring logic and the output format (e.g., a dashboard, alerts, or a weekly report.)


