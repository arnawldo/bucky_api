import pytest

from bucky_api import db
from bucky_api.models import User, BucketList, UserSchema, \
    BucketListSchema, Task


@pytest.fixture
def user(client):
    """A version of test client which has already
    registered a user <User username:arny, password:passy>
    """
    user = User(username='arny', password='passy')
    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def bucket(user):
    """A version of test client which has already
    created a bucket-list <BucketList name:my bucket> for
    user <User username:arny, password:passy>
    """
    bucket = BucketList(name="my bucket", user=user)
    db.session.add(bucket)
    db.session.commit()

    return bucket


# User schema
user_schema = UserSchema()
# BucketList schema
bucketlist_schema = BucketListSchema()


# USER SCHEMA TESTS
def test__serialized_user_has_correct_fields__succeeds(user):
    """Make sure a serialized user object has only username
     and id field"""
    user = User.query.first()
    # serialize user object
    result = user_schema.dump(user)
    # result.data == {
    # 'id': 1,
    # 'username': 'arny'
    # }

    assert result.data['username']
    assert result.data['id']
    with pytest.raises(KeyError):
        # password is not serialized
        result.data['password_hashed']


def test__id_and_password_cannot_be_deserialized__fails():
    """Make sure user json object with id field
    deserialized to dict does not include this fields"""

    json_data = {"id": 3,
                 "username": "arny",
                 "password": "passy"}

    # validate and deserialize json
    data, errors = user_schema.load(json_data)
    assert data['username']
    assert data['password']
    with pytest.raises(KeyError):
        data['id']


def test__error_if_username_not_found__fails():
    """Make sure user json object without username
    field produces an error"""
    json_data = {"id": 3,
                 "password": "passy"}

    # validate and deserialize json
    data, errors = user_schema.load(json_data)
    assert data['password']
    assert errors['username']


# BUCKET-LIST SCHEMA TESTS
def test__serialized_bucketlist_has_correct_fields__succeeds(bucket):
    """Make sure a serialized bucket-list object has only name,
    tasks and id field"""

    # create a task
    u = User.query.first()
    task = Task(description="first task",
                bucketlist=bucket,
                user=u)
    db.session.add(task)
    db.session.commit()
    # serialize bucket-list object
    result = bucketlist_schema.dump(bucket)
    # result.data == {
    # 'id': 1,
    # 'name': 'my bucket',
    # 'tasks': [{'id': 1, 'description': 'first task'},..]
    # }

    assert result.data['name']
    assert result.data['id']
    assert result.data['tasks']


def test__id_and_tasks_cannot_be_deserialized__fails():
    """Make sure bucketlist json object with id and tasks field
    deserialized to dict does not include these fields"""

    json_data = {"id": 3,
                 "name": "a bucket",
                 "tasks": [{"id": 1, "description": " a task"}]
                 }

    # validate and deserialize json
    data, errors = bucketlist_schema.load(json_data)
    assert data['name']
    with pytest.raises(KeyError):
        data['id']
    with pytest.raises(KeyError):
        data['tasks']


def test__error_if_name_not_found__fails():
    """Make sure bucket-list json object without name
    field produces an error"""
    json_data = {"some_field": "a bucket"}
    # validate and deserialize json
    data, errors = bucketlist_schema.load(json_data)
    assert errors['name']
