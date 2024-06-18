import threading
import time

from app_collect import init_collect, fetch_weather_entry_and_save


class BackgroundTask:
    def __init__(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        init_collect()
        while True:
            fetch_weather_entry_and_save()
            time.sleep(30)


def start_task():
    pass


background_task = BackgroundTask()
