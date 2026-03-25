# Trendscape Analysis for Partnership Development

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

**For detailed architecture,, evaluation metrics, and rationale, see the [Design Document](design.md).** 

### File Structure

```

Trendscape_Analysis_for_Partnership_Development/
├── dags/
│   └── market_intelligence_dag.py
├── src/
│   ├── config.py
│   ├── data_fetchers.py
│   ├── preprocessing.py
│   ├── topic_model.py
│   └── scoring.py
├── api/
│   ├── main.py
│   └── data/               # created at runtime
├── scripts/
│   ├── log_experiment.py
│   ├── monitor_drift.py
│   └── data_quality_check.py
├── tests/
│   ├── test_data_quality_ci.py
│   └── test_data_quality_local.py
├── notebooks/
│   └── exploratory_analysis.ipynb
├── .github/workflows/
│   └── market_intelligence.yml
├── dashboard.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── LICENSE
└── README.md

```

## Getting Started 

### Prerequisites

- Python 3.11
- Apache Spark 3.5.8
- Java 11 or 17 (if using SPark)
- Docker (options)

### Installation

1. Clone the repository:
  
```bash
   git clone https://github.com/AugustAllYear/Trendscape_Analysis_for_Partnership_Development.git
   cd Trendscape_Analysis_for_Partnership_Development.git
```
   
2. Create and activate a virtual environment:

```bash
   python3.11 -m venv vevn --prompt trendscape
   source venv/bin/activate  #Linux/macOS
   # .\venv\Scripts\activate  # Windows
```
   
3. Install dependencies:

```bash
   pip install --upgrade pip
   pip install -r requirements.txt
```
    
4. Download requiremed NLP models (this will be doen automatically on the first run, but you can pre-downlaod):
     
```bash
   python -m spacy download en_core_web_sm
   python -m nltk.downloader stopwords punkt
```
   
5. Set up environment variables (create a .env file or export):

```bash
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
  5. Initialize Airflow:

```bash
   airflow db init
   airflow users create \
   --username create \
   --firstname Admin \
   --lastname User \
   --role Admin \
   --email admin@example.com \
   --password admin
```

### Configuration

The pipeline uses environment variables for paths. You can set them as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_PATH` | `./data` | Base directory for raw and processed data |
| `MODEL_PATH` | `./models` | Directory for saved models |
| `OUTPUT_PATH` | `./data/output` | Directory for recommendation CSV files |
| `API_DATA_PATH` | `./api/data` | Directory for API data (metrics, recommendations JSON) |
| `API_URL` | `http://localhost:8000` | URL of the FastAPI service (used by dashboard) |

For local development, simply create the default directories:

```bash
mkdir -p data/staging data/processed data/output models api/data
```

```bash
mkdir -p api/data
```

## Environment Variables

Create a `.env` file in the project root with your API keys and optional path overrides. Example:

```bash
NEWSAPI_KEY=your_key_here
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
```
### Testing

Two sets of tests are provided:

- **CI (GitHub Actions)** - 'test.test_data_quality_ci.py' uses synthetic data and runs without external files.
- **Local** - 'test.test_data_quality_local.py' reads actual data from 'STAGING_PATH'. It will skip if no data is found. To run it, ensure you have at least one Paquet file in './data/staging'.

Run all tests with:
```bash
pytest test/
```

### Running Locally 

Note: 
The pipeline expects data and model directories. By default, it uses `./data/staging`, `./data/processed`, `./models`, etc. You can create them with:
```bash
mkdir -p data/staging data/processed data/output models api/data
```
If you want to use different locations, set the environment variables DATA_PATH, MODEL_PATH, OUTPUT_PATH before running Airflow or the API.

1. Start an Airflow scheduler and webserver (inseperate terminals):

```bash
   airflow schedules
   #in another terminal
   airflow webserver --port 8080
```

   Access the UI at http://localhost:8080


3. Trigger the DAG manually or wait for the schedules run.

4. Start the FASTAPI service:

```bash
    uvicorn api.main:app --reload --port 8000
```
    
API documentation available at http://localhost:8000/docs

### Running with Docker
Build the image:

```bash
    docker build -t trendscape .
    
```

Run the container:

```bash
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

### Testing 

- **CI (GitHub Actions)**: The workflow runs 'pytest tests/test_data_quality_ci.py' - these tests use synthetic data and do not require real files.
- **Local testing**: To test with actual data, create the necessary data files. (see 'Running Locally') and run 'pytest tests/test_data_quality_local.py'. these tests expect the data to be present at the paths defined in your environment. 

### View Results (FastAPI endpoint)

To view the recommendations you have 2 options:
Option 1: Copy and paste the following url into your browser or click the link here: 
http://localhost:8000/partner-recommendations?min_score=0.5&limit=10

Option 2:
Run this in a terminal
    
```bash
    curl "http://localhost:8000/partner-recommendations?min_score=0.5&limit=10"
```

Please note this returns only final partnership score (for ease of interpretability) which includes: company_name, mention_count, freq_score, sentiment_score, alignment_score, partnership_score.

### Airflow Import Errors

Ensure your virtual environment is activated and AIRFLOW_HOME is set correctly. Use the constraints file if dependency conflicts arise.

#### Data Folders Not Found

If you see errors about missing directories, create them manually:

```bash
    mkdir -p data/stagging data/processed data/output models api/data

```

Or set the environment cariables DATA_Path, MODEL_PATH to point to existing locations.

## License
See LICENSE

## Contact
For questions, contact the augustvollbrecht@proton.me.