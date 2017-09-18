import pytest

from bucky_api import db
from bucky_api.models import User, BucketList, Task


@pytest.fixture
def user(client):
    """A version of test client which has already
    registered a user <User username:arny, password:passy>
    """
    user = User(username='arny', password='passy')
    db.session.add(user)
    db.session.commit()

    return user


# USER MODEL
def test__user_can_be_created__succeeds(user):
    """Make sure a user instance can be created"""

    # check user exists in db
    u = User.query.first()
    assert u
    assert u.username == 'arny'
    assert user.username == 'arny'


def test__user_password_hashing_works__succeeds(user):
    """Make sure user password is write only,
    stored hashed, and can be verified"""

    with pytest.raises(AttributeError):
        user.password
    assert user.password_hashed != 'passy'
    assert user.verify_password('passy')


def test__user_can_generate_token__succeeds(user):
    """Make sure user can generate token that can be verified"""
    token = user.generate_auth_token(expiration=10)
    verified_user = User.verify_auth_token(token)
    assert verified_user.id == user.id
    unverified_user = User.verify_auth_token("junk")
    assert unverified_user is None


def test__user_has_custom_repr__succeeds(user):
    """Make sure user object has custom text representation"""
    assert 'User <arny>' in user.__repr__()


# BUCKET-LIST MODEL
def test__bucketlist_can_be_created__succeeds(user):
    """Make sure a bucket-list can be created"""
    bucket = BucketList(name="my bucket", user=user)
    db.session.add(bucket)
    db.session.commit()
    b = BucketList.query.first()
    assert b
    assert b.name == "my bucket"


def test__bucketlist_has_custom_repr__succeeds(user):
    """Make sure bucket-list object has custom text representation"""
    bucket = BucketList(name="my bucket", user=user)
    db.session.add(bucket)
    db.session.commit()
    assert 'BucketList <my bucket>' in bucket.__repr__()


# TASK MODEL
def test__task_can_be_created__succeeds(user):
    """Make sure a task can be created"""
    bucket = BucketList(name="my bucket", user=user)
    db.session.add(bucket)
    db.session.commit()
    task = Task(description="my task", user=user, bucketlist=bucket)
    db.session.add(task)
    db.session.commit()
    t = Task.query.first()
    assert t
    assert t.description == "my task"


def test__task_has_custom_repr__succeeds(user):
    """Make sure task object has custom text representation"""
    bucket = BucketList(name="my bucket", user=user)
    db.session.add(bucket)
    db.session.commit()
    task = Task(description="my task", user=user, bucketlist=bucket)
    db.session.add(task)
    db.session.commit()
    assert 'Task <my task>' in task.__repr__()
