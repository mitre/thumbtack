import logging
import os
from pkg_resources import get_distribution, DistributionNotFound

from flask import Flask, current_app
from flask_restful import Api

from .manager import MountManager
from .resources import Mount,  SupportedLibraries
from .views import main

try:
    __version__ = get_distribution('thumbtack').version
except DistributionNotFound:
    __version__ = 'Could not find version'


def create_app(image_dir=None):
    app = Flask(__name__)
    app.config.from_object('thumbtack.config')
    # Since development doesn't have this environment variable, it won't do anything
    app.config.from_envvar('THUMBTACK_CONFIG_PRODUCTION', silent=True)

    IMAGE_DIR = os.environ.get("IMAGE_DIR")
    MOUNT_DIR = os.environ.get("MOUNT_DIR")

    if IMAGE_DIR:
        app.config.update(IMAGE_DIR=IMAGE_DIR)

    # image_dir is used in the thumbtack entry point, and overwrites the environment variable
    if image_dir:
        app.config.update(IMAGE_DIR=image_dir)

    if MOUNT_DIR:
        app.config.update(MOUNT_DIR=MOUNT_DIR)

    configure(app)

    app.before_first_request(before_first_request)

    return app


def configure(app):
    configure_extensions(app)
    configure_blueprints(app)
    app.logger.info('configured')


def configure_extensions(app):
    app.logger.info('configuring extensions')
    api = Api(app)

    mount_manager = MountManager()
    api.add_resource(Mount,
                     '/mounts/<path:image_path>',
                     '/mounts/',
                     resource_class_kwargs={'mount_manager': mount_manager})
    api.add_resource(SupportedLibraries, '/supported', endpoint='supported')


def configure_blueprints(app):
    app.logger.info('configuring blueprints')
    app.register_blueprint(main)


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

        # app.logger.addHandler(fhandler)
        app.logger.addHandler(shandler)


def start_app():
    image_dir = os.getcwd()
    app = create_app(image_dir=image_dir)
    app.run(debug=True)
