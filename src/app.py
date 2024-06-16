import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go

CSV_FILE_PATH = './src/weather_data.csv'

st.set_page_config(layout="wide")  # Set the page layout to wide

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
    col1, col2 = st.columns([1, 1])  # Adjust column widths

    # Wind Line Chart
    fig_wind = px.line(data_tables['wind'], x='timestamp', y=['windAvg', 'windMin', 'windMax'], title='Wind Speed Over Time')
    st.plotly_chart(fig_wind, use_container_width=True)

    # Temperature Line Chart
    fig_temp = px.line(data_tables['temperature'], x='timestamp', y='temperature', title='Temperature Over Time')
    st.plotly_chart(fig_temp, use_container_width=True)



    col3, col4 = st.columns([3, 3])  # Adjust column widths
    with col3:
        # Wind Degrees Polar Plot
        if not data_tables['windDegrees'].empty:
            latest_wind_deg = data_tables['windDegrees']['windDegrees'].iloc[-1]
            fig_polar = go.Figure(go.Scatterpolar(
                r=[1],
                theta=[latest_wind_deg],
                mode='markers',
                marker=dict(size=14, color='red')
            ))

            fig_polar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=False),
                ),
                showlegend=False,
                title='Wind Direction'
            )
            st.plotly_chart(fig_polar, use_container_width=True)
