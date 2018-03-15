import json

import pytest

from thumbtack import create_app


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
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
