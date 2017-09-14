from flask import current_app


def test__app_is_in_testing_mode__succeeds(client):
    """Make sure test client is configured for testing"""
    assert current_app
    assert current_app.config['TESTING']
