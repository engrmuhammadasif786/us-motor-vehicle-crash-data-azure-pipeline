"""Streamlit dashboard for FARS crash data visualization."""

import os

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="FARS Crash Data Dashboard",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 U.S. Motor Vehicle Crash Data Dashboard")
st.markdown("""
This dashboard visualizes fatal crash data from the **Fatality Analysis Reporting System (FARS)**.
Data is processed through an end-to-end pipeline: Azure Blob Storage → Snowflake/DuckDB → dbt transformations.
""")

# Determine environment and connect to database
env = os.getenv("ENV", "dev")

if env == "dev":
    db_path = os.getenv("DUCKDB_PATH", "./data/dev.duckdb")
    con = duckdb.connect(db_path, read_only=True)
    fact_table = "main_marts.fct_accidents"
else:
    # Snowflake connection for production
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "PROD")
    import snowflake.connector
    con = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    )
    fact_table = f"{database}.{schema}_MARTS.FCT_ACCIDENTS"

# Load data
@st.cache_data(ttl=600)
def load_data():
    query = f"""
        SELECT
            crash_date,
            crash_year,
            crash_month,
            state_name,
            fatalities,
            drunk_drivers,
            total_vehicles,
            light_condition,
            weather_condition,
            manner_of_collision
        FROM {fact_table}
        ORDER BY crash_date
    """
    return con.execute(query).fetchdf()


try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
selected_years = st.sidebar.multiselect(
    "Select Years",
    options=sorted(df["crash_year"].unique()),
    default=sorted(df["crash_year"].unique())[-5:],
)

selected_states = st.sidebar.multiselect(
    "Select States",
    options=sorted(df["state_name"].unique()),
    default=[],
)

# Apply filters
filtered_df = df[df["crash_year"].isin(selected_years)]
if selected_states:
    filtered_df = filtered_df[filtered_df["state_name"].isin(selected_states)]

# Metrics
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Crashes", f"{len(filtered_df):,}")
col2.metric("Total Fatalities", f"{filtered_df['fatalities'].sum():,}")
col3.metric("Avg Fatalities/Crash", f"{filtered_df['fatalities'].mean():.2f}")
col4.metric("States", f"{filtered_df['state_name'].nunique()}")

st.markdown("---")

# Row 1: Two tiles as required by project
st.subheader("Crash Analysis")

# Tile 1: Distribution by categorical data (Light Condition)
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### 💡 Crash Distribution by Light Condition")
    light_counts = (
        filtered_df.groupby("light_condition")
        .size()
        .reset_index(name="crash_count")
        .sort_values("crash_count", ascending=True)
    )
    
    fig_light = px.bar(
        light_counts,
        x="crash_count",
        y="light_condition",
        orientation="h",
        color="crash_count",
        color_continuous_scale="Blues",
        title="Number of Crashes by Light Condition",
        labels={"light_condition": "Light Condition", "crash_count": "Crash Count"},
    )
    fig_light.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_light, use_container_width=True)

# Tile 2: Distribution across temporal line (Yearly trend)
with col_right:
    st.markdown("#### 📅 Crash Trend Over Time")
    yearly_counts = (
        filtered_df.groupby("crash_year")
        .size()
        .reset_index(name="crash_count")
    )
    
    fig_trend = px.line(
        yearly_counts,
        x="crash_year",
        y="crash_count",
        markers=True,
        title="Number of Crashes by Year",
        labels={"crash_year": "Year", "crash_count": "Crash Count"},
    )
    fig_trend.update_traces(line_color="#e74c3c", marker_size=8)
    fig_trend.update_layout(height=400)
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# Additional insights
st.subheader("Additional Insights")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### 🗺️ Top 10 States by Crash Count")
    state_counts = (
        filtered_df.groupby("state_name")
        .size()
        .reset_index(name="crash_count")
        .sort_values("crash_count", ascending=False)
        .head(10)
    )
    
    fig_states = px.bar(
        state_counts,
        x="state_name",
        y="crash_count",
        color="crash_count",
        color_continuous_scale="Reds",
        title="Top 10 States by Number of Crashes",
        labels={"state_name": "State", "crash_count": "Crash Count"},
    )
    fig_states.update_layout(height=350)
    st.plotly_chart(fig_states, use_container_width=True)

with col_b:
    st.markdown("#### 🌤️ Crashes by Weather Condition")
    weather_counts = (
        filtered_df.groupby("weather_condition")
        .size()
        .reset_index(name="crash_count")
        .sort_values("crash_count", ascending=False)
        .head(8)
    )
    
    fig_weather = px.pie(
        weather_counts,
        values="crash_count",
        names="weather_condition",
        title="Crash Distribution by Weather",
        hole=0.4,
    )
    fig_weather.update_layout(height=350)
    st.plotly_chart(fig_weather, use_container_width=True)

# Footer
st.markdown("---")
st.caption(f"""
Data source: [NHTSA FARS](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars) | 
Environment: {'Development (DuckDB)' if env == 'dev' else 'Production (Snowflake)'} | 
Pipeline: Prefect → Azure Blob → dbt → {'DuckDB' if env == 'dev' else 'Snowflake'}
""")
