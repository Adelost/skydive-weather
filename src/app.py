import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta

CSV_FILE_PATH = './src/weather_data.csv'

def set_page_config():
    st.set_page_config(layout="wide")

def display_title():
    st.title('Weather Data Visualization')

@st.cache_data
def load_csv_data(filepath):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        st.error(f"CSV file at {filepath} not found.")
        return pd.DataFrame(columns=['timestamp', 'windAvg', 'windDegrees', 'windMin', 'windMax', 'temperature'])

def convert_timestamp_to_datetime(data):
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    return data

def filter_data_last_hours(data, hours=8):
    now = datetime.now()
    time_threshold = now - timedelta(hours=8)
    return data[data['timestamp'] >= time_threshold]

def initialize_data_tables(filtered_data):
    return {
        'temperature': filtered_data[['timestamp', 'temperature']].dropna(),
        'wind': filtered_data[['timestamp', 'windAvg', 'windMin', 'windMax']].dropna(),
        'windDegrees': filtered_data[['timestamp', 'windDegrees']].dropna()
    }

def plot_wind_chart(data):
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    max_timestamp = data['timestamp'].max()
    min_timestamp = max_timestamp - pd.Timedelta(hours=1)

    fig = px.line(data, x='timestamp', y=['windAvg', 'windMin', 'windMax'], title='Wind Speed Over Time')
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=0, y1=8, fillcolor="green", opacity=0.2, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=8, y1=11, fillcolor="yellow", opacity=0.1, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=11, y1=14, fillcolor="red", opacity=0.1, layer="below", line_width=0)
    fig.update_xaxes(range=[min_timestamp, max_timestamp])
    st.plotly_chart(fig)

def plot_temperature_chart(data):
    fig = px.line(data, x='timestamp', y='temperature', title='Temperature Over Time')
    fig.update_yaxes(range=[0, 30])
    st.plotly_chart(fig)


def plot_wind_direction_chart(data):
    latest_wind_deg = data['windDegrees'].iloc[-1]
    fig = go.Figure(go.Scatterpolar(r=[1], theta=[latest_wind_deg], mode='markers', marker=dict(size=14, color='red')))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=False, title='Wind Direction')
    st.plotly_chart(fig)

def main():
    set_page_config()
    display_title()
    data = load_csv_data(CSV_FILE_PATH)
    data = convert_timestamp_to_datetime(data)
    filtered_data = filter_data_last_hours(data)
    data_tables = initialize_data_tables(filtered_data)

    placeholder = st.empty()
    with placeholder.container():
        plot_wind_chart(data_tables['wind'])
        plot_temperature_chart(data_tables['temperature'])
        plot_wind_direction_chart(data_tables['windDegrees'])

if __name__ == "__main__":
    main()