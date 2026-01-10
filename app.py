import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
API_KEY = os.getenv("EMBER_API_KEY")

# Page config
st.set_page_config(
    page_title="China Clean Energy Tracker",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6B7280;
        margin-top: 0;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1E3A5F;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stMetric {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .stMetric label {
        font-size: 1rem !important;
        color: #64748b !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #1e293b !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
    }
    p, li {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Color palette for energy sources
SOURCE_COLORS = {
    'Solar': '#F59E0B',
    'Wind': '#3B82F6',
    'Hydro': '#06B6D4',
    'Nuclear': '#8B5CF6',
    'Bioenergy': '#10B981',
    'Other renewables': '#6EE7B7',
    'Coal': '#6B7280',
    'Gas': '#F97316',
    'Oil': '#78716C',
    'Other fossil': '#9CA3AF',
}

CLEAN_SOURCES = ['Solar', 'Wind', 'Hydro', 'Nuclear', 'Bioenergy', 'Other renewables']
FOSSIL_SOURCES = ['Coal', 'Gas', 'Oil', 'Other fossil']

# Header
st.markdown('<p class="main-header">China Clean Energy Tracker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monthly electricity generation by source · Data from Ember</p>', unsafe_allow_html=True)
st.markdown("---")

# Fetch data
@st.cache_data(ttl=3600)
def fetch_data():
    base_url = "https://api.ember-energy.org"
    endpoint = "/v1/electricity-generation/monthly"
    params = {
        "entity_code": "CHN",
        "is_aggregate_series": "false",
        "start_date": "2015-01",
        "api_key": API_KEY
    }
    response = requests.get(f"{base_url}{endpoint}", params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    return None

data = fetch_data()

if data:
    df = pd.DataFrame(data)

    # Parse dates
    if {'year', 'month'}.issubset(df.columns):
        df['date'] = pd.to_datetime(dict(year=df['year'], month=df['month'], day=1))
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Identify series column
    series_col = next((col for col in ['series', 'fuel', 'source'] if col in df.columns), None)

    if series_col and 'generation_twh' in df.columns:
        # Pivot data
        df_pivot = df.pivot_table(
            index='date',
            columns=series_col,
            values='generation_twh'
        ).sort_index()

        # Calculate clean vs fossil
        clean_cols = [c for c in df_pivot.columns if c in CLEAN_SOURCES]
        fossil_cols = [c for c in df_pivot.columns if c in FOSSIL_SOURCES]
        source_cols = [c for c in df_pivot.columns if c in SOURCE_COLORS]

        df_pivot['Clean Energy'] = df_pivot[clean_cols].sum(axis=1)
        df_pivot['Fossil Fuels'] = df_pivot[fossil_cols].sum(axis=1)
        df_pivot['Total'] = df_pivot['Clean Energy'] + df_pivot['Fossil Fuels']
        df_pivot['Clean %'] = (df_pivot['Clean Energy'] / df_pivot['Total'] * 100)

        # Latest data
        latest = df_pivot.iloc[-1]
        latest_date = df_pivot.index[-1]

        # YoY comparison
        year_ago_idx = latest_date - pd.DateOffset(years=1)
        year_ago = df_pivot[df_pivot.index <= year_ago_idx].iloc[-1] if len(df_pivot[df_pivot.index <= year_ago_idx]) > 0 else None

        # ===================
        # KPI CARDS
        # ===================
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            clean_pct = latest['Clean %']
            delta = f"+{clean_pct - year_ago['Clean %']:.1f}pp" if year_ago is not None else None
            st.metric(
                label="Clean Energy Share",
                value=f"{clean_pct:.1f}%",
                delta=delta
            )

        with col2:
            total_gen = latest['Total']
            delta = f"{((total_gen / year_ago['Total']) - 1) * 100:.1f}%" if year_ago is not None else None
            st.metric(
                label="Total Generation",
                value=f"{total_gen:.0f} TWh",
                delta=delta
            )

        with col3:
            solar_gen = latest.get('Solar', 0)
            solar_yoy = f"{((solar_gen / year_ago.get('Solar', 1)) - 1) * 100:.0f}%" if year_ago is not None and year_ago.get('Solar', 0) > 0 else None
            st.metric(
                label="Solar Generation",
                value=f"{solar_gen:.1f} TWh",
                delta=solar_yoy
            )

        with col4:
            wind_gen = latest.get('Wind', 0)
            wind_yoy = f"{((wind_gen / year_ago.get('Wind', 1)) - 1) * 100:.0f}%" if year_ago is not None and year_ago.get('Wind', 0) > 0 else None
            st.metric(
                label="Wind Generation",
                value=f"{wind_gen:.1f} TWh",
                delta=wind_yoy
            )

        st.markdown(f"*Latest data: {latest_date.strftime('%B %Y')}*")

        # ===================
        # GENERATION BY SOURCE
        # ===================
        st.markdown('<p class="section-header">Generation by Source</p>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            # Stacked area chart
            source_totals = df_pivot[source_cols].sum().sort_values(ascending=False)
            ordered_sources = source_totals.index.tolist()

            fig = go.Figure()
            for source in reversed(ordered_sources):  # Reverse for proper stacking order
                fig.add_trace(go.Scatter(
                    x=df_pivot.index,
                    y=df_pivot[source],
                    name=source,
                    mode='lines',
                    stackgroup='one',
                    line=dict(width=0.5, color=SOURCE_COLORS.get(source, '#999999')),
                    fillcolor=SOURCE_COLORS.get(source, '#999999'),
                    hovertemplate=f'<b>{source}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}} TWh<extra></extra>'
                ))

            fig.update_layout(
                height=500,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title='',
                yaxis_title='Generation (TWh)',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                hovermode='closest',
                plot_bgcolor='#fafafa',
                paper_bgcolor='#fafafa',
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Latest Month Mix**")

            pie_data = latest[source_cols].dropna()
            pie_data = pie_data[pie_data > 0].sort_values(ascending=False)

            fig = go.Figure(data=[go.Pie(
                labels=pie_data.index,
                values=pie_data.values,
                marker_colors=[SOURCE_COLORS.get(s, '#999999') for s in pie_data.index],
                textinfo='label+percent',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>%{value:.1f} TWh<br>%{percent}<extra></extra>'
            )])

            fig.update_layout(
                height=450,
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
                paper_bgcolor='#fafafa'
            )
            st.plotly_chart(fig, use_container_width=True)

        # ===================
        # CLEAN ENERGY
        # ===================
        st.markdown('<p class="section-header">Clean Energy</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Clean Energy Generation Over Time**")

            fig = go.Figure()
            for source in clean_cols:
                fig.add_trace(go.Scatter(
                    x=df_pivot.index,
                    y=df_pivot[source],
                    name=source,
                    mode='lines',
                    stackgroup='one',
                    line=dict(width=0.5, color=SOURCE_COLORS.get(source, '#999999')),
                    fillcolor=SOURCE_COLORS.get(source, '#999999'),
                    hovertemplate=f'<b>{source}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}} TWh<extra></extra>'
                ))

            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title='',
                yaxis_title='Generation (TWh)',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                hovermode='closest',
                plot_bgcolor='#fafafa',
                paper_bgcolor='#fafafa',
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Clean Energy Share of Total**")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_pivot.index,
                y=df_pivot['Clean %'],
                mode='lines',
                fill='tozeroy',
                line=dict(color='#10B981', width=3),
                fillcolor='rgba(16, 185, 129, 0.3)',
                hovertemplate='<b>Clean Share</b><br>%{x|%b %Y}<br>%{y:.1f}%<extra></extra>'
            ))

            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title='',
                yaxis_title='Share (%)',
                hovermode='closest',
                plot_bgcolor='#fafafa',
                paper_bgcolor='#fafafa',
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        # Clean vs Fossil
        st.markdown("**Clean vs Fossil Fuels**")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_pivot.index,
            y=df_pivot['Clean Energy'],
            name='Clean Energy',
            mode='lines',
            line=dict(color='#10B981', width=3),
            hovertemplate='<b>Clean Energy</b><br>%{x|%b %Y}<br>%{y:.1f} TWh<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=df_pivot.index,
            y=df_pivot['Fossil Fuels'],
            name='Fossil Fuels',
            mode='lines',
            line=dict(color='#6B7280', width=3),
            hovertemplate='<b>Fossil Fuels</b><br>%{x|%b %Y}<br>%{y:.1f} TWh<extra></extra>'
        ))

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title='',
            yaxis_title='Generation (TWh)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
            hovermode='closest',
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
            font=dict(size=14)
        )
        st.plotly_chart(fig, use_container_width=True)

        # ===================
        # GROWTH TRENDS
        # ===================
        st.markdown('<p class="section-header">Growth Trends</p>', unsafe_allow_html=True)

        # Calculate YoY growth for each source
        df_yoy = df_pivot[source_cols].pct_change(periods=12) * 100

        # Latest YoY growth
        latest_yoy = df_yoy.iloc[-1].dropna().sort_values(ascending=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Year-over-Year Growth by Source** ({latest_date.strftime('%B %Y')})")

            colors = ['#10B981' if v > 0 else '#EF4444' for v in latest_yoy.values]

            fig = go.Figure(go.Bar(
                x=latest_yoy.values,
                y=latest_yoy.index,
                orientation='h',
                marker_color=colors,
                text=[f'{v:.1f}%' for v in latest_yoy.values],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>%{x:.1f}% YoY<extra></extra>'
            ))

            fig.update_layout(
                height=450,
                margin=dict(l=0, r=50, t=10, b=0),
                xaxis_title='Year-over-Year Growth (%)',
                yaxis_title='',
                plot_bgcolor='#fafafa',
                paper_bgcolor='#fafafa',
                font=dict(size=14)
            )
            fig.add_vline(x=0, line_color='#374151', line_width=1)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Solar & Wind Growth Trends**")

            fig = go.Figure()
            if 'Solar' in df_yoy.columns:
                fig.add_trace(go.Scatter(
                    x=df_yoy.index,
                    y=df_yoy['Solar'],
                    name='Solar',
                    mode='lines',
                    line=dict(color='#F59E0B', width=2.5),
                    hovertemplate='<b>Solar</b><br>%{x|%b %Y}<br>%{y:.1f}% YoY<extra></extra>'
                ))
            if 'Wind' in df_yoy.columns:
                fig.add_trace(go.Scatter(
                    x=df_yoy.index,
                    y=df_yoy['Wind'],
                    name='Wind',
                    mode='lines',
                    line=dict(color='#3B82F6', width=2.5),
                    hovertemplate='<b>Wind</b><br>%{x|%b %Y}<br>%{y:.1f}% YoY<extra></extra>'
                ))

            fig.update_layout(
                height=450,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title='',
                yaxis_title='YoY Growth (%)',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                hovermode='closest',
                plot_bgcolor='#fafafa',
                paper_bgcolor='#fafafa',
                font=dict(size=14)
            )
            fig.add_hline(y=0, line_color='#374151', line_width=1, line_dash='dash')
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Failed to fetch data from Ember API. Please check your API key.")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #9CA3AF; font-size: 1rem;'>"
    "Data source: <a href='https://ember-climate.org/' target='_blank'>Ember</a> · "
    "Updated monthly"
    "</p>",
    unsafe_allow_html=True
)
