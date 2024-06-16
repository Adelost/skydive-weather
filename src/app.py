import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta
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
    time_threshold = now - timedelta(hours=hours)
    return data[data['timestamp'] >= time_threshold]


def initialize_data_tables(filtered_data):
    return {
        'temperature': filtered_data[['timestamp', 'temperature']].dropna(),
        'wind': filtered_data[['timestamp', 'windDegrees', 'windAvg', 'windMin', 'windMax']].dropna(),
    }

def plot_wind_chart2(data):
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    max_timestamp = data['timestamp'].max()
    min_timestamp = max_timestamp - pd.Timedelta(hours=8)

    fig = px.line(data, x='timestamp', y=['windAvg', 'windMin', 'windMax'], title='Wind Speed Over Time')
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=0, y1=7, fillcolor="green", opacity=0.2, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=7, y1=11, fillcolor="yellow", opacity=0.1, layer="below",
                  line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=11, y1=20, fillcolor="red", opacity=0.1, layer="below", line_width=0)
    fig.update_xaxes(range=[min_timestamp, max_timestamp])
    fig.update_yaxes(range=[0, 13])
    st.plotly_chart(fig)


def plot_wind_chart(data):
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    max_timestamp = data['timestamp'].max()
    min_timestamp = max_timestamp - pd.Timedelta(hours=8)

    # Define custom colors for each line
    color_map = {
        'windAvg': 'royalblue',  # Blue for average wind speed
        'windMin': 'cyan',  # Green for minimum wind speed
        'windMax': 'red'  # Red for maximum wind speed
    }

    # Create the figure with a layout
    fig = go.Figure()

    # Add traces
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['windMin'], mode='lines', name='Minimum Wind Speed',
                             line=dict(color=color_map['windMin'], width=0)))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['windAvg'], mode='lines', name='Average Wind Speed', line=dict(color=color_map[
        'windAvg'], width=0), fill='tonexty'))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['windMax'], mode='lines', name='Maximum Wind Speed', line=dict(color=color_map[
        'windMax'], width=0), fill='tonexty'))

    # Adding background color bands
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=0, y1=7, fillcolor="green", opacity=0.2, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=7, y1=11, fillcolor="yellow", opacity=0.1, layer="below",
                  line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=11, y1=20, fillcolor="firebrick", opacity=0.1, layer="below",
                  line_width=0)

    # Set the range of the x and y axes
    fig.update_xaxes(range=[min_timestamp, max_timestamp])
    fig.update_yaxes(range=[0, 12])

    # Display the figure
    st.plotly_chart(fig)

def plot_temperature_chart(data):
    fig = px.line(data, x='timestamp', y='temperature', title='Temperature Over Time')
    st.plotly_chart(fig)


def adjust_timestamp_to_gmt2(data):
    GMT_OFFSET_MS = 2 * 60 * 60 * 1000
    data['timestamp'] = pd.to_datetime(data['timestamp'] + GMT_OFFSET_MS, unit='ms')
    return data


def plot_wind_direction_chart(data):
    # Assuming 'windDegrees', 'windAvg', and 'windMax' are columns in 'data'
    last_direction = data.iloc[-1]['windDegrees']
    last_wind_avg = min(data.iloc[-1]['windAvg'], 11)  # Ensuring the maximum value for wind average is 11
    last_wind_max = min(data.iloc[-1]['windMax'], 11)  # Getting the maximum wind speed

    # Direction bins and labels setup
    direction_bins = np.arange(0, 361, 45)
    direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

    # Find the category for the last direction
    last_direction_category = pd.cut([last_direction], bins=direction_bins, labels=direction_labels, right=False, include_lowest=True)[0]

    # Create DataFrame with all zeros for average wind speed and max wind speed
    all_zeros_avg = np.zeros(len(direction_labels))
    all_zeros_max = np.zeros(len(direction_labels))
    summary_data = pd.DataFrame({
        'direction_category': direction_labels,
        'windAvg': all_zeros_avg,
        'windMax': all_zeros_max  # Include windMax column
    })

    # Set only the last direction values for windAvg and windMax
    index = direction_labels.index(last_direction_category)
    summary_data.at[index, 'windAvg'] = last_wind_avg
    summary_data.at[index, 'windMax'] = last_wind_max  # Set max wind speed at the same index

    # Create the polar bar plot for wind average
    fig = px.bar_polar(summary_data, r='windAvg', theta='direction_category',
                       title='Wind Direction',
                       template="plotly_dark",
                       range_r=[0, 12],
                       color_discrete_sequence=["cyan"],  # Set bar colors to cyan
                       barmode='overlay')  # Bars will overlay for clarity

    # Add polar bars for maximum wind speed
    fig.add_trace(go.Barpolar(
        r=summary_data['windMax'],
        theta=summary_data['direction_category'],
        name='Max Wind Speed',
        marker_color='cyan',
        opacity=0.2,
    ))
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig)


def display_map():
    latitude = st.text_input("Latitude", value=55.923210902289945)
    longitude = st.text_input("Longitude", value=14.09258495388121)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        st.error("Please enter valid latitude and longitude values")
        return

    view_state = pdk.ViewState(latitude=latitude, longitude=longitude, zoom=14)
    map_style = 'mapbox://styles/mapbox/satellite-v9'
    deck = pdk.Deck(initial_view_state=view_state, map_style=map_style)
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
        col1, col2 = st.columns([2, 1])
        with col1:
            plot_wind_chart(data_tables['wind'])
        with col2:
            plot_wind_direction_chart(data_tables['wind'])
        plot_temperature_chart(data_tables['temperature'])
        display_map()


if __name__ == "__main__":
    main()
