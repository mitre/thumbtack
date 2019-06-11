import json
import os

import pytest

from thumbtack import create_app


@pytest.fixture(scope='module')
def test_client():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    image_dir = os.path.join(dir_path, 'test_images')

    flask_app = create_app(image_dir=image_dir, database='database.db')
    flask_app.config['MOUNT_DIR'] = os.path.join(dir_path, 'thumbtack_test_mount_dir')
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()


@pytest.fixture()
def expected_test_results():

    with open('expected-test-results.json', 'r') as f:
        disk_images = json.load(f)

    return disk_images
