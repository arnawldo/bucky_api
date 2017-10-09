import json
from base64 import b64encode

import pytest

from bucky_api import db
from bucky_api.common import status
from bucky_api.models import User

TOKEN_ENDPOINT = '/api/v1.0/auth/get_token/'
USER_ENDPOINT = '/api/v1.0/auth/users/'


@pytest.fixture
def client_with_user(client):
    """A version of test client which has already
     registered a user <User username:arny, password:passy>
    """
    response = client.post(USER_ENDPOINT,
                           data=json.dumps({'username': 'arny',
                                            'password': 'passy'}),
                           content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    return client


def get_api_headers(username, password):
    """Helper function for creating request headers with http authentication"""
    return {
        'Authorization': 'Basic ' + b64encode(
            (username + ':' + password).encode('utf-8')).decode('utf-8'),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }


# VERIFICATION TESTS
def test__unverified_access_to_protected_resources__fails(client):
    """Make sure unauthenticated requests to protected resources
    are rejected
     """
    # no credentials
    response = client.get(TOKEN_ENDPOINT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert b'Unauthorized Access' in response.data
    # invalid credentials
    response = client.get(TOKEN_ENDPOINT,
                          headers=get_api_headers('wrong', 'cred'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test__verified_user_get_token__success(client_with_user):
    """Make sure registered user can get a token"""
    response = client_with_user.get(TOKEN_ENDPOINT,
                                    headers=get_api_headers('arny', 'passy'))
    assert response.status_code == status.HTTP_200_OK
    assert b'token' in response.data
    assert b'expiration' in response.data


def test__access_protected_resources_with_token__success(client_with_user):
    """Make sure registered user can access protected resources with
    a token"""
    # get token
    response = client_with_user.get(TOKEN_ENDPOINT,
                                    headers=get_api_headers('arny', 'passy'))
    assert response.status_code == status.HTTP_200_OK
    assert b'token' in response.data
    assert b'expiration' in response.data
    json_data = json.loads(response.data.decode('utf-8'))
    token = json_data['token']
    # access protected resource with token
    user = User.query.first()  # User <arny>
    response = client_with_user.get(USER_ENDPOINT + str(user.id),
                                    headers=get_api_headers(token, ''))
    assert response.status_code == status.HTTP_200_OK
    assert b'arny' in response.data


def test__get_new_token_using_current_token__fails(client_with_user):
    """Make sure registered user can access protected resources with
    a token"""
    # get token
    response = client_with_user.get(TOKEN_ENDPOINT,
                                    headers=get_api_headers('arny', 'passy'))
    assert response.status_code == status.HTTP_200_OK
    json_data = json.loads(response.data.decode('utf-8'))
    token = json_data['token']
    # get new token
    response = client_with_user.get(TOKEN_ENDPOINT,
                                    headers=get_api_headers(token, ''))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert b'Invalid credentials' in response.data


# USER COLLECTION RESOURCE TESTS
def test__bad_request_returns_error__succeeds(client):
    """Make sure post request with no data sent
    returns error
    """
    response = client.post(USER_ENDPOINT)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert b'No input data provided' in response.data


def test__wrong_json_returns_error__succeeds(client):
    """Make sure post request with poorly formatted
    json returns error
    """
    response = client.post(USER_ENDPOINT,
                           data=json.dumps({'wrongfield': 'arny',
                                            'pass': 'passy'}),
                           content_type='application/json')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert b'Missing data for required field' in response.data
    assert b'username' in response.data
    assert b'password' in response.data


def test__register_user__succeeds(client):
    """Make sure user can register"""
    response = client.post(USER_ENDPOINT,
                           data=json.dumps({'username': 'arny',
                                            'password': 'passy'}),
                           content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert b'User registered' in response.data


def test__register_existing_user__fails(client_with_user):
    """Make sure user can register"""
    response = client_with_user.post(USER_ENDPOINT,
                                     data=json.dumps({'username': 'arny',
                                                      'password': 'passy'}),
                                     content_type='application/json')
    assert response.status_code == status.HTTP_409_CONFLICT
    assert b'This username already exist' in response.data


# USER RESOURCE TESTs
def test__retieve_existing_user__succeeds(client_with_user):
    """Make sure registered user can retrieve details"""
    user = User.query.first()  # User <arny>
    response = client_with_user.get(USER_ENDPOINT + str(user.id),
                                    headers=get_api_headers('arny', 'passy'))
    assert response.status_code == status.HTTP_200_OK
    assert b'arny' in response.data


def test__retieve_non_existing_user__fails(client_with_user):
    """Make sure user cannot retrieve non existent user details"""
    response = client_with_user.get(USER_ENDPOINT + "9999999",
                                    headers=get_api_headers('arny', 'passy'))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'User does not exist' in response.data


def test__change_password_with_correct_data__succeeds(client_with_user):
    """Make sure existing and rightful user with proper
     request can change their password
     """
    user = User.query.first()  # User <arny>
    response = client_with_user.patch(USER_ENDPOINT + str(user.id),
                                      headers=get_api_headers('arny', 'passy'),
                                      data=json.dumps({'username': 'arny',
                                                       'password': 'passi'}),
                                      content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert b'arny' in response.data


def test__change_password_with_no_data__fails(client_with_user):
    """Make sure existing user sending no data cannot change
    their password
    """
    user = User.query.first()  # User <arny>
    response = client_with_user.patch(USER_ENDPOINT + str(user.id),
                                      headers=get_api_headers('arny', 'passy'),
                                      data=json.dumps({})
                                      )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert b'No input data provided' in response.data


def test__change_password_with_wrong_data__fails(client_with_user):
    """Make sure existing and rightful user with improper
     request cannot change their password
     """
    user = User.query.first()  # User <arny>
    response = client_with_user.patch(USER_ENDPOINT + str(user.id),
                                      headers=get_api_headers('arny', 'passy'),
                                      data=json.dumps({'uname': 'arny',
                                                       'pass': 'passi'}),
                                      content_type='application/json')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert b'Missing data for required field' in response.data
    assert b'username' in response.data
    assert b'password' in response.data


def test__change_password_of_another_user__fails(client_with_user):
    """Make sure existing user cannot change password of another
     user
     """
    user = User.query.first()  # User <arny>
    user2 = User(username='harry', password='test')
    db.session.add(user2)
    db.session.commit()

    # harry trying to change arny's password
    response = client_with_user.patch(USER_ENDPOINT + str(user.id),
                                      data=json.dumps({'username': 'arny',
                                                       'password': 'test'}),
                                      headers=get_api_headers('harry', 'test'),
                                      content_type='application/json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert b'Forbidden' in response.data


def test__change_password_of_non_existent_user__fails(client_with_user):
    """Make sure existing user cannot change password of non
    existent user
     """
    response = client_with_user.patch(USER_ENDPOINT + "99999",
                                      data=json.dumps({'username': 'arny',
                                                       'password': 'passy'}),
                                      headers=get_api_headers('arny', 'passy'),
                                      content_type='application/json')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'User does not exist' in response.data
