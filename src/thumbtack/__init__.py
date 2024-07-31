import logging
import os
import threading

from pathlib import Path
from pkg_resources import get_distribution, DistributionNotFound

import click

from flask import Flask, current_app

from .directory_monitoring import DirectoryMonitoring
from .utils import init_db, monitor_image_dir
from .views import main


try:
    __version__ = get_distribution("thumbtack").version
except DistributionNotFound:
    __version__ = "Could not find version"


def create_app(mount_dir=None, image_dir=None, database=None, base_url=None, path_contains=None, skip_subdirectory=None, remove_directories=None):

    if base_url:
        static_url_path = f"{base_url}/static"
        app = Flask(__name__, static_url_path=static_url_path)
    else:
        app = Flask(__name__)

    # priority goes to command line args, then ENV variables, then val from config.py
    # configure defaults
    app.config.from_object("thumbtack.config")

    # configure from ENV variables
    if mount_dir:
        app.config.update(MOUNT_DIR=mount_dir)
    elif os.environ.get("THUMBTACK_MOUNT_DIR"):
        app.config.update(MOUNT_DIR=os.environ.get("THUMBTACK_MOUNT_DIR"))

    if image_dir:
        app.config.update(IMAGE_DIR=image_dir)
    elif os.environ.get("THUMBTACK_IMAGE_DIR"):
        app.config.update(IMAGE_DIR=os.environ.get("THUMBTACK_IMAGE_DIR"))

    if database:
        app.config.update(DATABASE=database)
    elif os.environ.get("THUMBTACK_DATABASE"):
        app.config.update(DATABASE=os.environ.get("THUMBTACK_DATABASE"))

    if base_url:
        app.config.update(APPLICATION_ROOT=base_url)
    elif os.environ.get("THUMBTACK_APPLICATION_ROOT"):
        app.config.update(APPLICATION_ROOT=os.environ.get("THUMBTACK_APPLICATION_ROOT"))

    if path_contains:
        app.config.update(PATH_CONTAINS=path_contains)

    if skip_subdirectory:
        app.config.update(SKIP_SUBDIRECTORY=skip_subdirectory)

    if remove_directories:
        app.config.update(REMOVE_DIRECTORIES=remove_directories)

    app.mnt_mutex = threading.Lock()

    # configure the rest
    configure(app, base_url)
    configure_logging(app)
    return app


def configure(app, base_url=None):

    app.logger.info("configuring extensions")

    static_folder = "static"
    if base_url:
        static_url_path = f"{base_url}/{static_folder}"
    else:
        static_url_path = static_folder

    app.register_blueprint(
        main,
        static_folder=static_folder,
        static_url_path=static_url_path,
        url_prefix=base_url,
    )

    # WARNING!
    # At app startup, this deletes the current, local sqlite database and creates a new one.
    # this may be confusing if it didn't clean up after itself previously and images are still mounted,
    # but not tracked by a new instance of the DB.
    db_file = Path(app.config["DATABASE"])

    with app.app_context():
        if db_file.is_file():
            db_file.unlink()

        if not db_file.is_file():
            init_db()
    app.logger.info("configured")


def configure_logging(app):
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s.%(module)s: %(message)s"
    )

    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)

        # In production mode, add log handler to sys.stderr.
        shandler = logging.StreamHandler()
        shandler.setLevel(logging.INFO)
        shandler.setFormatter(formatter)
        # app.logger.addHandler(shandler)


@click.command()
@click.option(
    "-d",
    "--debug",
    default=False,
    is_flag=True,
    help="Run the Thumbtack server in debug mode",
)
@click.option(
    "-h",
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host to run Thumbtack server on",
)
@click.option(
    "-p",
    "--port",
    default="8208",
    show_default=True,
    help="Port to run Thumbtack server on",
)
@click.option(
    "-m",
    "--mount-dir",
    help="Directory to mount disk images  [Default: /mnt/thumbtack]",
)
@click.option(
    "-i",
    "--image-dir",
    help="Directory of disk images for Thumbtack server to monitor  [Default: $CWD]",
)
@click.option("--db", "database", help="SQLite database to store mount state")
@click.option(
    "-b",
    "--base-url",
    default="/",
    show_default=True,
    help="Base URL where Thumbtack is hosted on the server",
)
@click.option(
    "--path-contains",
    default=None,
    show_default=True,
    help="Only select files containing specified string in the path",
)
@click.option(
    '-s',
    "--skip-subdirectory",
    multiple=True,
    default=[],
    show_default=True,
    help="Subdirectory to ignore when monitoring files",
)
@click.option(
    '-r',
    "--remove-directories",
    default=False,
    is_flag=True,
    help="Unmount all mountpoints and remove all empty directories in the thumbtack mount directory",
)
def start_app(debug, host, port, mount_dir, image_dir, database, base_url, path_contains, skip_subdirectory, remove_directories):
    app = create_app(
        mount_dir=mount_dir, image_dir=image_dir, database=database, base_url=base_url, path_contains=path_contains, skip_subdirectory=skip_subdirectory, remove_directories=remove_directories,
    )
    directory_monitoring_thread = DirectoryMonitoring(app)
    directory_monitoring_thread.start()
    app.run(debug=debug, host=host, port=port)
