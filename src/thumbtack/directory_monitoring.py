import threading
import time

from .utils import monitor_image_dir, startup_remove_dirs


class DirectoryMonitoring(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app

    def run(self):
        with self.app.app_context():
            try:
                if self.app.config["REMOVE_DIRECTORIES"]:
                    startup_remove_dirs()
            except (KeyError, TypeError):
                pass
            while True:
                time.sleep(3)
                monitor_image_dir()
