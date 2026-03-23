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
