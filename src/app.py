import os
import pandas as pd
import streamlit as st
import plotly.graph_objs as go

CSV_FILE_PATH = './src/weather_data.csv'

st.title('Weather Data Visualization')

# Load data from CSV
@st.cache_data
def load_csv_data(filepath):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        st.error(f"CSV file at {filepath} not found.")
        return pd.DataFrame(columns=['timestamp', 'windAvg', 'windDegrees', 'windMin', 'windMax', 'temperature'])

data = load_csv_data(CSV_FILE_PATH)

# Convert timestamp to datetime
data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

# Initialize data tables for Streamlit charts
data_tables = {
    'temperature': data[['timestamp', 'temperature']].dropna(),
    'wind': data[['timestamp', 'windAvg', 'windMin', 'windMax']].dropna(),
    'windDegrees': data[['timestamp', 'windDegrees']].dropna()
}

# Create charts
placeholder = st.empty()
with placeholder.container():
    col1, col2 = st.columns(2)
    with col1:
        st.line_chart(data_tables['temperature'].set_index('timestamp'))
    with col2:
        st.line_chart(data_tables['wind'].set_index('timestamp'))
    col3, col4 = st.columns(2)
    with col3:
        st.line_chart(data_tables['windDegrees'].set_index('timestamp'))
    with col4:
        if not data_tables['windDegrees'].empty:
            latest_wind_deg = data_tables['windDegrees']['windDegrees'].iloc[-1]
            fig = go.Figure(go.Scatterpolar(
                r=[1],
                theta=[latest_wind_deg],
                mode='markers',
                marker=dict(size=14, color='red')
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=False),
                ),
                showlegend=False
            )
            st.plotly_chart(fig)