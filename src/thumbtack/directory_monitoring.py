import threading
import time

from .utils import monitor_image_dir


class DirectoryMonitoring(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app

    def run(self):
        with self.app.app_context():
            while True:
                time.sleep(3)
                monitor_image_dir()
