import os
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("EMBER_API_KEY")

# Base API settings
base_url = "https://api.ember-energy.org"
annual_endpoint = "/v1/electricity-generation/yearly"
monthly_endpoint = "/v1/electricity-generation/monthly"
carbon_intensity_endpoint = "/v1/carbon-intensity/yearly"

# Common parameters for generation and carbon intensity
gen_raw_params = {
    "entity_code": "CHN",
    "is_aggregate_series": "false",
    "start_year": "2000",
    "api_key": API_KEY
}
gen_agg_params = gen_raw_params.copy()
gen_agg_params["is_aggregate_series"] = "true"
ci_params = {"entity_code": "CHN", "start_year": "2000", "api_key": API_KEY}

# Fetch aggregated annual generation for metrics
df_agg = pd.DataFrame()
resp_agg = requests.get(f"{base_url}{annual_endpoint}", params=gen_agg_params)
if resp_agg.status_code == 200:
    df_agg = pd.DataFrame(resp_agg.json().get("data", []))
    if 'date' in df_agg.columns:
        df_agg['year'] = pd.to_datetime(df_agg['date'], errors='coerce').dt.year

# Fetch carbon intensity data
df_ci = pd.DataFrame()
resp_ci = requests.get(f"{base_url}{carbon_intensity_endpoint}", params=ci_params)
if resp_ci.status_code == 200:
    df_ci = pd.DataFrame(resp_ci.json().get("data", []))
    if 'date' in df_ci.columns:
        df_ci['year'] = pd.to_datetime(df_ci['date'], errors='coerce').dt.year

# Fetch raw annual generation for charts
df_ann_pivot = pd.DataFrame()
resp_gen_raw = requests.get(f"{base_url}{annual_endpoint}", params=gen_raw_params)
if resp_gen_raw.status_code == 200:
    df_gen_raw = pd.DataFrame(resp_gen_raw.json().get("data", []))
    if 'date' in df_gen_raw.columns:
        df_gen_raw['year'] = pd.to_datetime(df_gen_raw['date'], errors='coerce').dt.year
    series_col = next((c for c in ['fuel','source','series'] if c in df_gen_raw.columns), None)
    if series_col:
        df_ann_pivot = df_gen_raw.pivot_table(
            index='year', columns=series_col, values='generation_twh'
        ).sort_index()

# Fetch raw monthly generation for charts
df_mon_pivot = pd.DataFrame()
resp_mon_raw = requests.get(f"{base_url}{monthly_endpoint}", params=gen_raw_params)
if resp_mon_raw.status_code == 200:
    df_mon_raw = pd.DataFrame(resp_mon_raw.json().get("data", []))
    if {'year','month'}.issubset(df_mon_raw.columns):
        df_mon_raw['date'] = pd.to_datetime(
            dict(year=df_mon_raw['year'], month=df_mon_raw['month'], day=1)
        )
    elif 'date' in df_mon_raw.columns:
        df_mon_raw['date'] = pd.to_datetime(df_mon_raw['date'], errors='coerce')
    ser_mon = next((c for c in ['fuel','source','series'] if c in df_mon_raw.columns), None)
    if ser_mon:
        df_mon_pivot = df_mon_raw.pivot_table(
            index='date', columns=ser_mon, values='generation_twh'
        ).sort_index()

# Streamlit layout
st.title("China Energy Dashboard")
st.markdown("Kyle Chan")

# Metrics for latest year
if not df_agg.empty:
    latest_year = int(df_agg['year'].max())
    # Clean energy share
    if 'share_of_generation_pct' in df_agg.columns:
        clean = df_agg.loc[
            (df_agg['year']==latest_year) & (df_agg['series'].str.lower()=='clean'),
            'share_of_generation_pct'
        ].iloc[0]
        st.metric(label=f"Clean Energy Share {latest_year}", value=f"{clean:.1f}%")
    # Carbon intensity
    if not df_ci.empty:
        ci_col = next(c for c in df_ci.columns if 'intensity' in c.lower() and 'share' not in c.lower())
        ci = df_ci.loc[df_ci['year']==latest_year, ci_col].iloc[0]
        st.metric(label=f"Carbon Intensity {latest_year}", value=f"{ci:.1f} gCO₂/kWh")

# Annual generation chart
st.subheader("Electricity Generation by Source (Annual)")
st.markdown("Data: Ember")
if not df_ann_pivot.empty:
    st.line_chart(df_ann_pivot)
    latest = df_ann_pivot.iloc[-1].dropna()
    latest_pos = latest[latest > 0]
    if not latest_pos.empty:
        fig, ax = plt.subplots()
        ax.pie(latest_pos, labels=latest_pos.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title(f"Generation Share {latest_year}")
        st.pyplot(fig)

# Monthly generation chart
st.subheader("Electricity Generation by Source (Monthly)")

if not df_mon_pivot.empty:
    st.line_chart(df_mon_pivot)
    latest_m = df_mon_pivot.iloc[-1].dropna()
    latest_m_pos = latest_m[latest_m > 0]
    if not latest_m_pos.empty:
        figm, axm = plt.subplots()
        axm.pie(latest_m_pos, labels=latest_m_pos.index, autopct='%1.1f%%', startangle=90)
        axm.axis('equal')
        axm.set_title(f"Generation Share {df_mon_pivot.index[-1].strftime('%Y-%m')}")
        st.pyplot(figm)
