import json
import os
import time
import re
import requests
import csv
from threading import Thread
from flask import Flask, jsonify

BASE_WEATHER_URL = 'https://wx.awos.se/get.aspx?viewId=kristianstad-overview.html'
FETCH_INTERVAL = 30
CSV_FILE_PATH = 'weather_entries.csv'


app = Flask(__name__)

# Global variable to hold weather data
weather_entries = []


def extract_data(html, pattern):
    match = re.search(pattern, html)
    return float(match.group(1)) if match else float('nan')


def knots_to_meters_per_second(knots):
    return round(knots * 0.51444, 1)


def fetch_weather_entry():
    timestamp = int(time.time() * 1000)
    response = requests.get(f"{BASE_WEATHER_URL}&{timestamp}")
    html = response.text

    wind_avg1 = extract_data(html, r'MEAN02\s+\d+\/(\d+)')
    wind_avg2 = extract_data(html, r'MEAN02\s+\d+\/\d+ KT\s+\d+\/(\d+)')
    wind_degrees1 = extract_data(html, r'MEAN02\s+(\d+)\/\d+')
    wind_degrees2 = extract_data(html, r'MEAN02\s+\d+\/\d+ KT\s+(\d+)\/\d+')
    wind_min1 = extract_data(html, r'MIN\/MAX\s+(\d+)\/\d+')
    wind_max1 = extract_data(html, r'MIN\/MAX\s+\d+\/(\d+)')
    wind_min2 = extract_data(html, r'MIN\/MAX\s+\d+\/\d+\s+(\d+)\/\d+')
    wind_max2 = extract_data(html, r'MIN\/MAX\s+\d+\/\d+\s+\d+\/(\d+)')

    wind_avg = knots_to_meters_per_second((wind_avg1 + wind_avg2) / 2)
    wind_degrees = (wind_degrees1 + wind_degrees2) / 2
    wind_min = knots_to_meters_per_second(min(wind_min1, wind_min2))
    wind_max = knots_to_meters_per_second(max(wind_max1, wind_max2, wind_avg))
    temperature = extract_data(html, r'\bT\s+(\d+(\.\d+)?)')

    return {
        'timestamp': timestamp,
        'windAvg': wind_avg,
        'windDegrees': wind_degrees,
        'windMin': wind_min,
        'windMax': wind_max,
        'temperature': temperature,
    }


def load_csv_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    return []


def save_csv_data(filepath, data):
    with open(filepath, 'w', newline='') as file:
        fieldnames = ['timestamp', 'windAvg', 'windDegrees', 'windMin', 'windMax', 'temperature']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def update_csv_file(weather_entries):
    save_csv_data(CSV_FILE_PATH, weather_entries)


def filter_identical_rows(data, ignore_keys=['timestamp']):
    if not data:
        return data

    # Filter rows older than 24 hours
    current_time = int(time.time() * 1000)
    twenty_four_hours_ago = current_time - 24 * 2 * 60 * 60 * 1000
    data = [row for row in data if int(row['timestamp']) >= twenty_four_hours_ago]

    filtered_data = [data[0]]
    for i in range(1, len(data) - 1):
        if not rows_are_identical(data[i], data[i - 1], ignore_keys):
            filtered_data.append(data[i])
    # Always add last row
    if len(filtered_data) > 1:
        filtered_data.append(data[-1])
    return filtered_data


def rows_are_identical(row1, row2, ignore_keys):
    keys = set(row1.keys()) - set(ignore_keys)
    return all(row1[key] == row2[key] for key in keys)


def periodic_fetch():
    while True:
        fetch_weather_entry_and_save()
        time.sleep(FETCH_INTERVAL)


if __name__ == '__main__':
    # Load the existing CSV data into the global variable at startup
    weather_entries = load_csv_data(CSV_FILE_PATH)
    weather_entries = filter_identical_rows(weather_entries)
    # Start the periodic fetch thread
    fetch_thread = Thread(target=periodic_fetch, daemon=True)
    fetch_thread.start()

    # Run the Flask app
    app.run(debug=True, use_reloader=False)


def fetch_weather_entry_and_save():
    global weather_entries
    try:
        entry = fetch_weather_entry()
        print(entry)
        weather_entries.append(entry)
        weather_entries = filter_identical_rows(weather_entries)
        update_csv_file(weather_entries)
    except Exception as error:
        print('Failed to fetch weather data', error)
    return weather_entries
