import json
from base64 import b64encode

import pytest

from bucky_api import db
from bucky_api.common import status
from bucky_api.models import User, BucketList

BUCKETLIST_ENDPOINT = '/api/v1.0/bucketlists/'
USER_ENDPOINT = '/api/v1.0/auth/users/'


# TEST HELPERS
def get_api_headers(username, password):
    """Helper function for creating request headers with http authentication"""
    return {
        'Authorization': 'Basic ' + b64encode(
            (username + ':' + password).encode('utf-8')).decode('utf-8'),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }


# PY.TEST FIXTURES
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


@pytest.fixture
def client_with_user_n_bkt(client_with_user):
    """A version of test client which has already
     registered a user <User username:arny, password:passy> and
     created a bucket-list <BucketList name:buck>
    """
    # create bucket-list
    response = client_with_user.post(BUCKETLIST_ENDPOINT,
                                     headers=get_api_headers('arny', 'passy'),
                                     data=json.dumps({'name': 'buck'}),
                                     content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED

    return client_with_user


# BUCKET-LIST COLLECTION RESOURCE
def test__create_bucketlist_correct_request__succeeds(client_with_user):
    """
    Make sure request to create bucket-list that does not exist using
    proper request succeeds
    """
    response = client_with_user.post(BUCKETLIST_ENDPOINT,
                                     headers=get_api_headers('arny', 'passy'),
                                     data=json.dumps({'name': 'buck'}),
                                     content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert b'Created bucket-list'


def test__create_bucketlist_using_no_data__fails(client_with_user):
    """
    Make sure request to create bucket-list with no data
    returns an error
    """
    response = client_with_user.post(BUCKETLIST_ENDPOINT,
                                     headers=get_api_headers('arny', 'passy'),
                                     data=json.dumps({}),
                                     content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert b'No input data provided'


def test__create_bucketlist_using_wrong_data__fails(client_with_user):
    """
    Make sure request to create bucket-list with poorly formatted data
    returns an error
    """
    response = client_with_user.post(BUCKETLIST_ENDPOINT,
                                     headers=get_api_headers('arny', 'passy'),
                                     data=json.dumps({'wont_work': 'buck'}),
                                     content_type='application/json')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert b'name'


def test__create_bucketlist_that_already_exists__fails(client_with_user_n_bkt):
    """
    Make sure request to create bucket-list that already exists
    returns an error
    """

    # user tries to create existing bucket-list:buck
    response = (client_with_user_n_bkt.
                post(BUCKETLIST_ENDPOINT,
                     headers=get_api_headers('arny', 'passy'),
                     data=json.dumps({'name': 'buck'}),
                     content_type='application/json'))
    assert response.status_code == status.HTTP_409_CONFLICT
    assert b'Bucket-list already exists'


def test__get_bucketlists_with_pagination__succeeds(client_with_user):
    """Make sure a user can retrieve bucketlists in paginated format"""
    # create bucket-lists
    user = User.query.first()  # User <arny>
    bucket_names = ('buck', 'buck 2', 'buck 3', 'buck 4', 'buck 5')
    buckets = [BucketList(name=bucket_name, user=user)
               for bucket_name in bucket_names]
    db.session.add_all(buckets)
    db.session.commit()
    # ask for page 1 of bucketlists
    # should return 3 bucketlists per page
    response = client_with_user.get(BUCKETLIST_ENDPOINT,
                                    headers=get_api_headers('arny', 'passy'),
                                    query_string={'page': 1},
                                    content_type='application/json')
    assert b'buck 2' in response.data
    assert b'buck 5' not in response.data
    # ask for page 2 of bucketlists
    response = client_with_user.get(BUCKETLIST_ENDPOINT,
                                    headers=get_api_headers('arny', 'passy'),
                                    query_string={'page': 2},
                                    content_type='application/json')
    assert b'buck 5' in response.data
    assert b'buck 2' not in response.data


# INDIVIDUAL BUCKETLIST RESOURCE TEST
def test__retrieve_existing_bucketlist__succeeds(client_with_user_n_bkt):
    """
    Make sure user can retrieve an existing bucketlist
    """
    # retrieve bucket-list from db
    bucket = BucketList.query.first()

    response = (client_with_user_n_bkt.
                get(BUCKETLIST_ENDPOINT + str(bucket.id),
                    headers=get_api_headers('arny', 'passy')))
    assert response.status_code == status.HTTP_200_OK
    assert b'buck' in response.data


def test__retrieve_non_existing_bucketlist__fails(client_with_user):
    """
    Make sure user can not retrieve a bucket-list that does not exist
    """
    non_existent_bucket_id = "9999999"
    response = (client_with_user.
                get(BUCKETLIST_ENDPOINT + non_existent_bucket_id,
                    headers=get_api_headers('arny', 'passy')))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'Bucket-list not found' in response.data


def test__change_non_existent_bucketlist__fails(client_with_user):
    """
    Make sure user cannot alter a bucket-list that does not exist
    """
    non_existent_bucket_id = "9999999"
    response = (client_with_user.
                patch(BUCKETLIST_ENDPOINT + non_existent_bucket_id,
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({'name': 'buckyy'}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'Bucket-list not found' in response.data


def test__change_bucketlist_with_no_data__fails(client_with_user_n_bkt):
    """
    Make sure user cannot alter a bucket-list using request with no data
    """
    # retrieve bucket-list from db
    bucket = BucketList.query.first()

    response = (client_with_user_n_bkt.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id),
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert b'No input data provided' in response.data


def test__change_bucketlist_with_wrong_data__fails(client_with_user_n_bkt):
    """
    Make sure user cannot alter a bucket-list using poorly formatted data
    """
    # retrieve bucket-list from db
    bucket = BucketList.query.first()

    response = (client_with_user_n_bkt.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id),
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({'nm': 'buckyy'}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert b'name' in response.data


def test__alter_existing_bucketlist__succeeds(client_with_user_n_bkt):
    """
    Make sure user can alter an existing bucket-list using
    correct request
    """
    # retrieve bucket-list from db
    bucket = BucketList.query.first()

    # alter bucket-list
    response = (client_with_user_n_bkt.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id),
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({'name': 'backyy'}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_200_OK
    assert b'backyy' in response.data
    assert bucket.name == 'backyy'


def test__delete_existing_bucketlist__succeeds(client_with_user_n_bkt):
    """
    Make sure user can delete an existing bucketlist
     using correct request
    """
    # retrieve bucket-list from db
    bucket = BucketList.query.first()

    # delete bucket-list
    response = (client_with_user_n_bkt.
                delete(BUCKETLIST_ENDPOINT + str(bucket.id),
                       headers=get_api_headers('arny', 'passy')
                       ))
    assert response.status_code == status.HTTP_200_OK
    assert b'Deleted bucket-list' in response.data


def test__delete_non_existent_bucketlist__fails(client_with_user_n_bkt):
    """
    Make sure user cannot delete a non-existent bucket-list
    """
    non_existent_bucket_id = "9999999"
    response = (client_with_user_n_bkt.
                delete(BUCKETLIST_ENDPOINT + non_existent_bucket_id,
                       headers=get_api_headers('arny', 'passy')
                       ))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'Bucket-list does not exist' in response.data
