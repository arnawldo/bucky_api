import pytest
from bucky_api import create_app


@pytest.fixture
def app():

    app = create_app('testing')

    with app.app_context():
        yield app


@pytest.fixture
def client(request, app):

    client = app.test_client()

    def teardown():
        pass
    request.addfinalizer(teardown)

    return client
