from flask import Flask, jsonify
import requests
import re
import time
from threading import Thread
import streamlit as st
import pandas as pd

BASE_WEATHER_URL = 'https://wx.awos.se/get.aspx?viewId=kristianstad-overview.html'
FETCH_INTERVAL = 30
MAX_GRAPH_DURATION = 60 * 60

app = Flask(__name__)


def extract_data(html, pattern):
    match = re.search(pattern, html)
    return float(match.group(1)) if match else float('nan')


def knots_to_meters_per_second(knots):
    return round(knots * 0.51444, 1)


def fetch_weather_data():
    timestamp = int(time.time() * 1000)
    response = requests.get(f"{BASE_WEATHER_URL}&{timestamp}")
    html = response.text

    return {
        'windAvg': knots_to_meters_per_second(extract_data(html, r'WIND\s+\d+\/(\d+(\.\d+)?)')),
        'windDegrees': extract_data(html, r'WIND\s+(\d+)\/'),
        'windMin': knots_to_meters_per_second(extract_data(html, r'MIN\/MAX\s+(\d+(\.\d+)?)')),
        'windMax': knots_to_meters_per_second(extract_data(html, r'MIN\/MAX\s+\d+\/(\d+(\.\d+)?)')),
        'temperature': extract_data(html, r'\bT\s+(\d+(\.\d+)?)'),
    }


@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        data = fetch_weather_data()
        return jsonify(data)
    except Exception as error:
        return jsonify({'error': 'Failed to fetch weather data'}), 500


def periodic_fetch():
    while True:
        try:
            data = fetch_weather_data()
            print('Updated Weather Data:', data)
        except Exception as error:
            print('Failed to fetch weather data', error)
        time.sleep(FETCH_INTERVAL)


fetch_thread = Thread(target=periodic_fetch, daemon=True)
fetch_thread.start()

st.title('Real-time Weather Data Visualization')

data_tables = {
    'temperature': {'data': pd.DataFrame(columns=['time', 'temperature']), 'chart': st.line_chart()},
    'wind': {'data': pd.DataFrame(columns=['time', 'windAvg', 'windMin', 'windMax']), 'chart': st.line_chart()},
    'windDegrees': {'data': pd.DataFrame(columns=['time', 'windDegrees']), 'chart': st.line_chart()}
}


def update_data():
    weather_data = fetch_weather_data()
    current_time = pd.Timestamp.now()

    for key, value in weather_data.items():
        if key in data_tables:
            new_data = pd.DataFrame({'time': [current_time], key: [value]})
            data_table = data_tables[key]['data']
            data_table = pd.concat([data_table, new_data], ignore_index=True)
            data_table = data_table[data_table['time'] > (current_time - pd.Timedelta(seconds=MAX_GRAPH_DURATION))]
            data_tables[key]['data'] = data_table
            data_tables[key]['chart'].add_rows(data_table.set_index('time'))

    wind_data = pd.DataFrame({
        'time': [current_time],
        'windAvg': [weather_data['windAvg']],
        'windMin': [weather_data['windMin']],
        'windMax': [weather_data['windMax']]
    })
    data_tables['wind']['data'] = pd.concat([data_tables['wind']['data'], wind_data], ignore_index=True)
    data_tables['wind']['data'] = data_tables['wind']['data'][
        data_tables['wind']['data']['time'] > (current_time - pd.Timedelta(seconds=MAX_GRAPH_DURATION))]
    data_tables['wind']['chart'].add_rows(data_tables['wind']['data'].set_index('time'))


while True:
    update_data()
    time.sleep(FETCH_INTERVAL)