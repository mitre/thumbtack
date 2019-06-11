import logging
import os

from pathlib import Path
from pkg_resources import get_distribution, DistributionNotFound

import click

from flask import Flask, current_app
from flask_restful import Api

from .resources import Mount, SupportedLibraries
from .utils import init_db
from .views import main


try:
    __version__ = get_distribution('thumbtack').version
except DistributionNotFound:
    __version__ = 'Could not find version'


def create_app(image_dir=None, database=None):
    app = Flask(__name__)
    app.config.from_object('thumbtack.config')
    # Since development doesn't have this environment variable, it won't do anything
    app.config.from_envvar('THUMBTACK_CONFIG_PRODUCTION', silent=True)

    if os.environ.get("IMAGE_DIR"):
        app.config.update(IMAGE_DIR=os.environ.get("IMAGE_DIR"))
    if os.environ.get("MOUNT_DIR"):
        app.config.update(MOUNT_DIR=os.environ.get("MOUNT_DIR"))
    if os.environ.get("DATABASE"):
        app.config.update(DATABASE=os.environ.get("DATABASE"))

    # these variables are from the thumbtack entry point, and should overwrite environment variable equivalents
    if image_dir:
        app.config.update(IMAGE_DIR=image_dir)
    if database:
        app.config.update(DATABASE=database)

    configure(app)

    app.before_first_request(before_first_request)

    return app


def configure(app):
    configure_extensions(app)
    configure_blueprints(app)

    # WARNING!
    # At app startup, this deletes the current, local sqlite database and creates a new one.
    # this may be confusing if it didn't clean up after itself previously and images are still mounted,
    # but not tracked by a new instance of the DB.
    configure_database(app)
    app.logger.info('configured')


def configure_extensions(app):
    app.logger.info('configuring extensions')
    api = Api(app)

    api.add_resource(Mount,
                     '/mounts/<path:image_path>',
                     '/mounts/')
    api.add_resource(SupportedLibraries,
                     '/supported',
                     endpoint='supported')


def configure_blueprints(app):
    app.logger.info('configuring blueprints')
    app.register_blueprint(main)


def configure_database(app):
    db_file = Path(app.config['DATABASE'])

    with app.app_context():
        if db_file.is_file():
            db_file.unlink()

        if not db_file.is_file():
            init_db()


def before_first_request():
    configure_logging(current_app)


def configure_logging(app):
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s.%(module)s: %(message)s")

        shandler = logging.StreamHandler()
        shandler.setLevel(logging.DEBUG)
        shandler.setFormatter(formatter)

        # app.logger.addHandler(shandler)


@click.command()
@click.option('-d', '--debug', default=False, is_flag=True, help='Run the Thumbtack server in debug mode')
@click.option('-h', '--host', default='127.0.0.1',
              show_default=True, help='Host to run Thumbtack server on')
@click.option('-p', '--port', default='8208',
              show_default=True, help='Port to run Thumbtack server on')
@click.option('-i', '--image-dir', default=os.getcwd(),
              help='Directory of disk images for Thumbtack server to monitor  [Default: $CWD]')
@click.option('--db', 'database', default='database.db',
              show_default=True, help='SQLite database to store mount state')
def start_app(debug, host, port, image_dir, database):
    app = create_app(image_dir=image_dir, database=database)
    app.run(debug=debug, host=host, port=port)
