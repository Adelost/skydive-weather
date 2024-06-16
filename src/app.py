import os

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta
import streamlit as st
import pydeck as pdk

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
        'windDegrees': filtered_data[['timestamp', 'windDegrees', 'windAvg']].dropna()
    }


def plot_wind_chart(data):
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    max_timestamp = data['timestamp'].max()
    min_timestamp = max_timestamp - pd.Timedelta(hours=1)

    fig = px.line(data, x='timestamp', y=['windAvg', 'windMin', 'windMax'], title='Wind Speed Over Time')
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=0, y1=8, fillcolor="green", opacity=0.2, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=8, y1=11, fillcolor="yellow", opacity=0.1, layer="below",
                  line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=11, y1=14, fillcolor="red", opacity=0.1, layer="below", line_width=0)
    fig.update_xaxes(range=[min_timestamp, max_timestamp])
    st.plotly_chart(fig)


def plot_temperature_chart(data):
    fig = px.line(data, x='timestamp', y='temperature', title='Temperature Over Time')
    fig.update_yaxes(range=[0, 30])
    st.plotly_chart(fig)


def adjust_timestamp_to_gmt2(data):
    GMT_OFFSET_MS = 2 * 60 * 60 * 1000
    data['timestamp'] = pd.to_datetime(data['timestamp'] + GMT_OFFSET_MS, unit='ms')
    return data


def plot_wind_direction_chart(data):
    # Ensure data has correct data types
    data['windDegrees'] = data['windDegrees'].astype(float)
    data['windAvg'] = data['windAvg'].astype(float)

    # Define bins for wind direction
    direction_bins = np.arange(0, 361, 45)  # Include 360 to close the circle
    direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]  # No need to repeat 'N'
    data['direction_category'] = pd.cut(data['windDegrees'], bins=direction_bins, labels=direction_labels, right=False, include_lowest=True)

    # Aggregate average wind speeds per direction bin
    summary_data = data.groupby('direction_category').agg({'windAvg': 'mean'}).reset_index()

    # Create the wind rose chart
    fig = px.bar_polar(summary_data, r='windAvg', theta='direction_category',
                       color='windAvg', template="plotly_dark",
                       color_continuous_scale=px.colors.sequential.Plasma_r)

    fig.update_layout(
        title='Wind Rose Chart',
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, summary_data['windAvg'].max()]
            )
        )
    )

    st.plotly_chart(fig)

def display_map():
    center_coordinates = [55.923210902289945, 14.09258495388121]
    view_state = pdk.ViewState(
        latitude=center_coordinates[0],
        longitude=center_coordinates[1],
        zoom=14
    )
    map_style = 'mapbox://styles/mapbox/satellite-v9'
    deck = pdk.Deck(
        initial_view_state=view_state,
        map_style=map_style
    )
    st.pydeck_chart(deck)


def main():
    set_page_config()
    display_title()
    data = load_csv_data(CSV_FILE_PATH)
    data = adjust_timestamp_to_gmt2(data)
    data = convert_timestamp_to_datetime(data)
    data_tables = initialize_data_tables(data)

    placeholder = st.empty()
    with placeholder.container():
        with placeholder.container():
            col1, col2 = st.columns([2, 1])  # Create two columns with specified width ratios
            with col1:
                plot_wind_chart(data_tables['wind'])
            with col2:
                plot_wind_direction_chart(data_tables['windDegrees'])
            plot_temperature_chart(data_tables['temperature'])
            display_map()



if __name__ == "__main__":
    main()
