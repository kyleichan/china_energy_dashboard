import os
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
API_KEY = os.getenv("EMBER_API_KEY")

st.title("China: Electricity Generation by Source (Monthly)")
st.write("Data source: Ember")

# Request monthly electricity generation data for China
base_url = "https://api.ember-energy.org"
endpoint = "/v1/electricity-generation/monthly"
params = {
    "entity_code": "CHN",
    "is_aggregate_series": "false",
    "start_date": "2000-01",
    "api_key": API_KEY
}
response = requests.get(f"{base_url}{endpoint}", params=params)

if response.status_code == 200:
    data = response.json().get("data", [])
    df = pd.DataFrame(data)

    if df.empty:
        st.write("No data returned from API.")
    else:
        # Construct a datetime index for monthly data
        if {'year', 'month'}.issubset(df.columns):
            df['date'] = pd.to_datetime(dict(year=df['year'], month=df['month'], day=1))
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        else:
            st.write(f"Cannot find columns to parse date: {df.columns.tolist()}")
            st.stop()

        # Identify series column
        series_col = next((col for col in ['fuel', 'source', 'series'] if col in df.columns), None)
        if not series_col:
            st.write(f"No series column found: {df.columns.tolist()}")
            st.stop()

        # Pivot to wide format: each fuel as a column
        df_pivot = df.pivot_table(
            index='date',
            columns=series_col,
            values='generation_twh'
        ).sort_index()

        # Plot all fuel series over time
        st.line_chart(df_pivot)

        # Pie chart for the latest month: filter out non-positive values
        latest = df_pivot.iloc[-1].dropna()
        latest = latest[latest > 0]
        if not latest.empty:
            fig, ax = plt.subplots()
            ax.pie(latest, labels=latest.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            latest_date = latest.name.strftime('%Y-%m')
            ax.set_title(f"Share of Generation by Source for {latest_date}")
            st.pyplot(fig)
        else:
            st.write("No positive generation data available for the latest month to plot pie chart.")

        # Pie chart for the year 2024: sum monthly generation by source
        df['year'] = df['date'].dt.year
        annual_2024 = df[df['year'] == 2024]
        if not annual_2024.empty:
            annual_pivot = annual_2024.pivot_table(
                index=None,
                columns=series_col,
                values='generation_twh',
                aggfunc='sum'
            )
            annual = annual_pivot.iloc[0].dropna()
            annual = annual[annual > 0]
            if not annual.empty:
                fig2, ax2 = plt.subplots()
                ax2.pie(annual, labels=annual.index, autopct='%1.1f%%', startangle=90)
                ax2.axis('equal')
                ax2.set_title("Share of Generation by Source for 2024")
                st.pyplot(fig2)
            else:
                st.write("No positive generation data available for 2024 to plot pie chart.")
        else:
            st.write("No data available for 2024 to plot annual pie chart.")
else:
    st.error(f"Error fetching data: {response.status_code}")


