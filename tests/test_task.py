import json
from base64 import b64encode

import pytest

from bucky_api import db
from bucky_api.common import status
from bucky_api.models import User, BucketList, Task

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


@pytest.fixture
def client_with_user_n_bkt_n_task(client_with_user_n_bkt):
    """A version of test client which has already
     registered a user <User username:arny, password:passy>,
     created a bucket-list <BucketList name:buck>, and
     created a task <Task description:tasky>
    """
    bucket = BucketList.query.first()  # BucketList <name:bucky>
    # create task
    response = (client_with_user_n_bkt.
                post(BUCKETLIST_ENDPOINT + str(bucket.id) + '/tasks/',
                     headers=get_api_headers('arny', 'passy'),
                     data=json.dumps({'description': 'tasky'}),
                     content_type='application/json'))
    assert response.status_code == status.HTTP_201_CREATED

    return client_with_user_n_bkt


# BUCKET-LIST COLLECTION RESOURCE
def test__create_task_correct_request__succeeds(client_with_user_n_bkt):
    """
    Make sure request to create task that does not exist using
    proper request succeeds
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    response = (client_with_user_n_bkt.
                post(BUCKETLIST_ENDPOINT + str(bucket.id) + '/tasks/',
                     headers=get_api_headers('arny', 'passy'),
                     data=json.dumps({'description': 'tasky'}),
                     content_type='application/json'))
    assert response.status_code == status.HTTP_201_CREATED
    assert b'Task created'


def test__create_task_using_no_data__fails(client_with_user_n_bkt):
    """
    Make sure request to create task with no data
    returns an error
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    response = (client_with_user_n_bkt.
                post(BUCKETLIST_ENDPOINT + str(bucket.id) + '/tasks/',
                     headers=get_api_headers('arny', 'passy'),
                     data=json.dumps({}),
                     content_type='application/json'))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert b'No input data provided'


def test__create_task_using_wrong_data__fails(client_with_user_n_bkt):
    """
    Make sure request to create bucket-list with poorly formatted data
    returns an error
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    response = (client_with_user_n_bkt.
                post(BUCKETLIST_ENDPOINT + str(bucket.id) + '/tasks/',
                     headers=get_api_headers('arny', 'passy'),
                     data=json.dumps({'wont_work': 'tasky'}),
                     content_type='application/json'))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert b'description'


def test__create_task_that_already_exist__fails(client_with_user_n_bkt_n_task):
    """
    Make sure request to create task that already exists
    returns an error
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>

    # user tries to create existing task:tasky
    response = (client_with_user_n_bkt_n_task.
                post(BUCKETLIST_ENDPOINT + str(bucket.id) + '/tasks/',
                     headers=get_api_headers('arny', 'passy'),
                     data=json.dumps({'description': 'tasky'}),
                     content_type='application/json'))
    assert response.status_code == status.HTTP_409_CONFLICT
    assert b'This task already exists'


def test__get_tasks__succeeds(client_with_user_n_bkt):
    """Make sure a user can retrieve tasks"""
    # create tasks
    user = User.query.first()  # User <arny>
    bucket = BucketList.query.first()  # BucketList <buck>
    task_descriptions = ('task', 'task 2', 'task 3', 'task 4', 'task 5')
    tasks = [Task(description=task_descr,
                  bucketlist=bucket,
                  user=user)
             for task_descr in task_descriptions]
    db.session.add_all(tasks)
    db.session.commit()

    response = (client_with_user_n_bkt.
                get(BUCKETLIST_ENDPOINT + str(bucket.id) + '/tasks/',
                    headers=get_api_headers('arny', 'passy')))
    assert b'task 2' in response.data
    assert b'task 5' in response.data
    assert response.status_code == status.HTTP_200_OK


# INDIVIDUAL TASK RESOURCE TESTS


def test__change_non_existent_task__fails(client_with_user_n_bkt_n_task):
    """
    Make sure user cannot alter a task that does not exist
    """
    non_existent_task_id = "9999999"
    bucket = BucketList.query.first()  # BucketList <name:buck>
    response = (client_with_user_n_bkt_n_task.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id) +
                      '/tasks/' + non_existent_task_id,
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({'description': 'tasky'}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'Task does not exist' in response.data


def test__change_task_with_no_data__fails(client_with_user_n_bkt_n_task):
    """
    Make sure user cannot alter a task using request with no data
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    task = Task.query.first()  # Task <description:tasky>
    response = (client_with_user_n_bkt_n_task.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id) +
                      '/tasks/' + str(task.id),
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert b'No input data provided' in response.data


def test__change_task_with_wrong_data__fails(client_with_user_n_bkt_n_task):
    """
    Make sure user cannot alter a task using poorly formatted data
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    task = Task.query.first()  # Task <description:tasky>

    response = (client_with_user_n_bkt_n_task.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id) +
                      '/tasks/' + str(task.id),
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({'wrong': 'taski'}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert b'description' in response.data


def test__alter_existing_task__succeeds(client_with_user_n_bkt_n_task):
    """
    Make sure user can alter an existing task using
    correct request
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    task = Task.query.first()  # Task <description:tasky>

    response = (client_with_user_n_bkt_n_task.
                patch(BUCKETLIST_ENDPOINT + str(bucket.id) +
                      '/tasks/' + str(task.id),
                      headers=get_api_headers('arny', 'passy'),
                      data=json.dumps({'description': 'tasko'}),
                      content_type='application/json'))
    assert response.status_code == status.HTTP_200_OK
    assert b'tasko' in response.data
    assert task.description == 'tasko'
    assert b'Task modified' in response.data


def test__delete_existing_task__succeeds(client_with_user_n_bkt_n_task):
    """
    Make sure user can delete an existing task
     using correct request
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    task = Task.query.first()  # Task <description:tasky>

    response = (client_with_user_n_bkt_n_task.
                delete(BUCKETLIST_ENDPOINT + str(bucket.id) +
                       '/tasks/' + str(task.id),
                       headers=get_api_headers('arny', 'passy')
                       ))
    assert response.status_code == status.HTTP_200_OK
    assert b'Task deleted' in response.data


def test__delete_non_existent_task__fails(client_with_user_n_bkt_n_task):
    """
    Make sure user cannot delete a non-existent task
    """
    bucket = BucketList.query.first()  # BucketList <name:buck>
    non_existent_task_id = '99999999'
    response = (client_with_user_n_bkt_n_task.
                delete(BUCKETLIST_ENDPOINT + str(bucket.id) +
                       '/tasks/' + non_existent_task_id,
                       headers=get_api_headers('arny', 'passy')
                       ))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert b'Task does not exist' in response.data
