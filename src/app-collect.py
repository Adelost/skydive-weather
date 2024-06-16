import json
import os
import time
import re
import requests
from threading import Thread
from flask import Flask, jsonify

BASE_WEATHER_URL = 'https://wx.awos.se/get.aspx?viewId=kristianstad-overview.html'
FETCH_INTERVAL = 30
JSON_FILE_PATH = 'weather_data.json'

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
        'timestamp': timestamp,
        'windAvg': knots_to_meters_per_second(extract_data(html, r'WIND\s+\d+\/(\d+(\.\d+)?)')),
        'windDegrees': extract_data(html, r'WIND\s+(\d+)\/'),
        'windMin': knots_to_meters_per_second(extract_data(html, r'MIN\/MAX\s+(\d+(\.\d+)?)')),
        'windMax': knots_to_meters_per_second(extract_data(html, r'MIN\/MAX\s+\d+\/(\d+(\.\d+)?)')),
        'temperature': extract_data(html, r'\bT\s+(\d+(\.\d+)?)'),
    }


def load_json_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return []


def save_json_data(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)


def update_json_file(data):
    current_data = load_json_data(JSON_FILE_PATH)
    current_data.append(data)
    save_json_data(JSON_FILE_PATH, current_data)


@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        data = fetch_weather_data()
        update_json_file(data)
        return jsonify(data)
    except Exception as error:
        return jsonify({'error': 'Failed to fetch weather data'}), 500


def periodic_fetch():
    while True:
        try:
            data = fetch_weather_data()
            update_json_file(data)
            print('Updated Weather Data:', data)
        except Exception as error:
            print('Failed to fetch weather data', error)
        time.sleep(FETCH_INTERVAL)


fetch_thread = Thread(target=periodic_fetch, daemon=True)
fetch_thread.start()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
