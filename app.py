import os
import time

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta
import pydeck as pdk

from app_collect import fetch_weather_entry_and_save

CSV_FILE_PATH = 'weather_entries.csv'
SHOW_HOURS = 2


def set_page_config():
    st.set_page_config(layout="wide")


def display_title():
    # st.title('Weather Data Visualization')
    pass


def display_clock():
    placeholder = st.empty()
    now = datetime.utcnow() + timedelta(hours=2)  # Sweden is UTC+2
    current_time = now.strftime("%H:%M")
    placeholder.markdown(f"<h1 style='text-align: center;'>{current_time}</h1>", unsafe_allow_html=True)


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


def plot_wind_chart(data):
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    max_timestamp = data['timestamp'].max()
    min_timestamp = max_timestamp - pd.Timedelta(hours=SHOW_HOURS)

    # Filtering data for changes in wind speed and maintaining the last timestamp
    data['change_avg'] = data['windAvg'].diff().fillna(0)  # Use fillna(0) for the initial NaN in diff
    data['change_min'] = data['windMin'].diff().fillna(0)
    data['change_max'] = data['windMax'].diff().fillna(0)

    # Filter rows where there is a change in any of the wind measurement columns or it's the last timestamp
    filtered_data = data[
        (data['change_avg'] != 0) | (data['change_min'] != 0) | (data['change_max'] != 0) | (data['timestamp'] == max_timestamp)]

    # Define custom colors for each line
    color_map = {
        'windAvg': 'royalblue',  # Blue for average wind speed
        'windMin': 'royalblue',  # Cyan for minimum wind speed
        'windMax': 'firebrick'  # Red for maximum wind speed
    }

    # Create the figure with a layout
    fig = go.Figure()

    # Add traces for filtered data
    fig.add_trace(go.Scatter(x=filtered_data['timestamp'], y=filtered_data['windMin'], mode='lines', name='Minimum Wind Speed',
                             line=dict(color=color_map['windMin'], width=3)))
    fig.add_trace(go.Scatter(x=filtered_data['timestamp'], y=filtered_data['windAvg'], mode='lines', name='Average Wind Speed',
                             line=dict(color=color_map[
                                 'windAvg'], width=0), fill='tonexty'))
    fig.add_trace(go.Scatter(x=filtered_data['timestamp'], y=filtered_data['windMax'], mode='lines', name='Maximum Wind Speed',
                             line=dict(color=color_map[
                                 'windMax'], width=3), fill='tonexty'))

    # Adding background color bands
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=0, y1=6, fillcolor="green", opacity=0.1, layer="below", line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=6, y1=11, fillcolor="yellow", opacity=0.1, layer="below",
                  line_width=0)
    fig.add_shape(type="rect", x0=min_timestamp, x1=max_timestamp, y0=11, y1=20, fillcolor="firebrick", opacity=0.1, layer="below",
                  line_width=0)

    # Set the range of the x and y axes
    fig.update_xaxes(range=[min_timestamp, max_timestamp])
    fig.update_yaxes(range=[0, 12])
    fig.update_layout(
        title='Wind Speed',
        showlegend=False,
        margin=dict(l=0, r=150, t=50, b=0)  # Adjust margins
    )
    annotations = []
    current_temp = data['windAvg'].iloc[-1]
    current_time = data['timestamp'].iloc[-1]
    annotations.append(dict(
        xref='x', x=current_time, y=current_temp,
        xanchor='left', yanchor='middle',
        text='{} m/s'.format(current_temp),
        font=dict(family='Arial', size=16, color='white'),
        showarrow=False,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='white'
    ))

    fig.update_layout(annotations=annotations)

    # Display the figure
    st.plotly_chart(fig)


def plot_temperature_chart(data):
    # Convert timestamp to datetime if it isn't already
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    last_x_hours = data[data['timestamp'] >= (data['timestamp'].max() - pd.Timedelta(hours=SHOW_HOURS))]

    # Create a Plotly Graph Objects figure
    fig = go.Figure()

    # Add the temperature trace
    fig.add_trace(go.Scatter(
        x=last_x_hours['timestamp'],
        y=last_x_hours['temperature'],
        mode='lines',
        name='Temperature',
        line=dict(color="royalblue", width=3),  # Custom line width
        fill='tonexty'  # Fill to the next Y axis (essentially the x-axis in this single trace scenario)
    ))

    # Update layout to add titles and customize axes
    fig.update_layout(
        title='Temperature',
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        xaxis=dict(showgrid=True),  # Show grid lines for better readability
        yaxis=dict(showgrid=True),
    )
    fig.update_yaxes(range=[0, 30])

    # Add annotation for the current temperature value
    annotations = []
    current_temp = data['temperature'].iloc[-1]
    current_time = data['timestamp'].iloc[-1]
    annotations.append(dict(
        xref='x', x=current_time, y=current_temp,
        xanchor='left', yanchor='middle',
        text='{}°C'.format(current_temp),
        font=dict(family='Arial', size=16, color='white'),
        showarrow=False,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='white'
    ))
    fig.update_layout(
        margin=dict(l=0, r=150, t=50, b=0)  # Adjust margins
    )
    fig.update_layout(annotations=annotations)

    # Display the figure in a Streamlit app
    st.plotly_chart(fig)


def adjust_timestamp_to_gmt2(data):
    GMT_OFFSET_MS = 2 * 60 * 60 * 1000
    data['timestamp'] = pd.to_datetime(data['timestamp'] + GMT_OFFSET_MS, unit='ms')
    return data


def plot_wind_rose(data):
    # Assuming 'windDegrees', 'windAvg', and 'windMax' are columns in 'data'
    last_direction = data.iloc[-1]['windDegrees']
    last_wind_avg = min(data.iloc[-1]['windAvg'], 11)  # Ensuring the maximum value for wind average is 11
    last_wind_max = min(data.iloc[-1]['windMax'] - last_wind_avg, 11)  # Getting the maximum wind speed

    # Direction bins and labels setup
    direction_bins = np.arange(-22.5, 361, 45)
    direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]

    # Adjust the binning process to handle the circular nature of directions
    if last_direction >= 337.5 or last_direction < 22.5:
        last_direction_category = "N"
    elif 22.5 <= last_direction < 67.5:
        last_direction_category = "NE"
    elif 67.5 <= last_direction < 112.5:
        last_direction_category = "E"
    elif 112.5 <= last_direction < 157.5:
        last_direction_category = "SE"
    elif 157.5 <= last_direction < 202.5:
        last_direction_category = "S"
    elif 202.5 <= last_direction < 247.5:
        last_direction_category = "SW"
    elif 247.5 <= last_direction < 292.5:
        last_direction_category = "W"
    elif 292.5 <= last_direction < 337.5:
        last_direction_category = "NW"

    # Create DataFrame with all zeros for average wind speed and max wind speed
    all_zeros_avg = np.zeros(len(direction_labels) - 1)
    all_zeros_max = np.zeros(len(direction_labels) - 1)
    summary_data = pd.DataFrame({
        'direction_category': direction_labels[:-1],
        'windAvg': all_zeros_avg,
        'windMax': all_zeros_max  # Include windMax column
    })

    # Set only the last direction values for windAvg and windMax
    index = direction_labels[:-1].index(last_direction_category)
    summary_data.at[index, 'windAvg'] = last_wind_avg
    summary_data.at[index, 'windMax'] = last_wind_max  # Set max wind speed at the same index

    # Create the polar bar plot for wind average
    fig = px.bar_polar(summary_data, r='windAvg', theta='direction_category',
                       title='Wind Direction',
                       template="plotly_dark",
                       range_r=[0, 12],
                       color_discrete_sequence=["royalblue"],  # Set bar colors to cyan
                       barmode='overlay')  # Bars will overlay for clarity

    # Add polar bars for maximum wind speed
    fig.add_trace(go.Barpolar(
        r=summary_data['windMax'],
        theta=summary_data['direction_category'],
        name='Max Wind Speed',
        marker_color='firebrick',
        opacity=0.4,
    ))
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig)


def generate_ellipse_points(center, radius_x, radius_y, num_points=100):
    angles = np.linspace(0, 2 * np.pi, num_points)
    # Correct the aspect ratio based on latitude
    aspect_ratio = np.cos(np.radians(center[1]))
    return [[
        center[0] + (radius_x * np.cos(angle)) / aspect_ratio,
        center[1] + radius_y * np.sin(angle)
    ] for angle in angles]


def display_map():
    latitude = 55.923210902289945
    longitude = 14.09258495388121

    view_state = pdk.ViewState(latitude=latitude, longitude=longitude, zoom=12.5)
    map_style = 'mapbox://styles/mapbox/satellite-v9'

    ellipse_points = generate_ellipse_points([longitude, latitude], 0.005, 0.01)  # Adjust radii as needed

    # Define the oval layer
    oval_layer = pdk.Layer(
        "PolygonLayer",
        data=[{"coordinates": [ellipse_points], "name": "ellipse"}],
        get_polygon="coordinates",
        get_fill_color=[255, 0, 0, 100],  # Red color with some transparency
        get_line_color=[255, 0, 0, 255],  # Red outline
        line_width_min_pixels=2
    )

    landing_layer = pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [longitude, latitude]}],
        get_position="position",
        get_radius=100,  # Radius in meters
        get_fill_color=[0, 255, 0, 100],  # Green color with some transparency
    )

    deck = pdk.Deck(
        layers=[oval_layer, landing_layer],
        initial_view_state=view_state,
        map_style=map_style,
    )

    st.markdown("Spot", unsafe_allow_html=True)
    st.pydeck_chart(deck)


def plot_wind_direction_chart(data):
    # Convert timestamp to datetime if it isn't already
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    last_x_hours = data[data['timestamp'] >= (data['timestamp'].max() - pd.Timedelta(hours=SHOW_HOURS))]

    # Create a Plotly Graph Objects figure
    fig = go.Figure()

    # Add the wind direction trace
    fig.add_trace(go.Scatter(
        x=last_x_hours['timestamp'],
        y=last_x_hours['windDegrees'],
        mode='lines',
        name='Wind Direction',
        line=dict(color="royalblue", width=3),  # Custom line width
    ))

    # Update layout to add titles and customize axes
    fig.update_layout(
        title='Wind Direction',
        xaxis_title='Time',
        yaxis_title='Wind Direction (Degrees)',
        xaxis=dict(showgrid=True),  # Show grid lines for better readability
        yaxis=dict(showgrid=True),
    )
    fig.update_yaxes(range=[0, 360])  # Wind direction ranges from 0 to 360 degrees

    # Display the figure in a Streamlit app
    st.plotly_chart(fig)


def main():
    set_page_config()
    display_title()

    # Create a persistent placeholder for the clock outside the loop
    clock_placeholder = st.empty()

    while True:
        fetch_weather_entry_and_save()
        data = load_csv_data(CSV_FILE_PATH)
        data = adjust_timestamp_to_gmt2(data)
        data = convert_timestamp_to_datetime(data)
        data_tables = initialize_data_tables(data)

        # Use the persistent placeholder to display the clock without blocking the rest of the app
        with clock_placeholder.container():
            display_clock()

            # Plot data charts
            plot_wind_chart(data_tables['wind'])
            col2, col3 = st.columns([1, 1])
            with col2:
                plot_wind_rose(data_tables['wind'])
            with col3:
                plot_wind_direction_chart(data_tables['wind'])
            plot_temperature_chart(data_tables['temperature'])
            display_map()

        time.sleep(30)


if __name__ == "__main__":
    main()
