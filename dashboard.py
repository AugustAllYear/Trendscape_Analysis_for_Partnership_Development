import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Trendscape Dashboard", layout='wide')
st.title("Market Intelligence Dashboard")

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Sidebar
st.sidebar.header("Filters")
min_score = st.sidebar.slider("Minimum partnership score", 0.0, 1.0, 0.3)
limit = st.sidebar.slider("Number of recommendations", 1, 50, 10)

# Fetch recommendations
try:
    response = requests.get(f"{API_URL}/partner-recommendations",
                            params={"min_score": min_score, "limit": limit})
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        st.subheader("Top Partnership Recommendations")
        st.dataframe(df)
        # Bar chart
        fig = px.bar(df, x='company', y='partnership_score', color='partnership_score',
                     title='Partnership Scores')
        st.plotly_chart(fig)
    else:
        st.error("Could not fetch recommendations")
except Exception as e:
    st.error(f"API connection error: {e}")

# Fetch model metrics
try:
    metrics = requests.get(f"{API_URL}/model-metrics").json()
    st.subheader("Model Health Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Topics", metrics.get('n_topics', 'N/A'))
    col2.metric("Outlier Ratio", f"{metrics.get('outlier_ratio', 0):.2%}")
    col3.metric("Avg Topic Probability", f"{metrics.get('avg_topic_probability', 0):.3f}")
except Exception as e:
    st.info("Model metrics not yet available")

# Fetch trending topics
st.subheader("Trending Topics")
try:
    topics = requests.get(f"{API_URL}/trending-topics?limit=5").json()
    for topic in topics:
        st.write(f"- {topic.get('topic_words', 'N/A')} (growth: {topic.get('growth', 'N/A')})")
except:
    pass