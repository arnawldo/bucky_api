from flask import current_app
from itsdangerous import Serializer
from marshmallow import Schema, fields, validate
from werkzeug.security import generate_password_hash, check_password_hash

from bucky_api import db

######## MODELS ########

class User(db.Model):
    """Class for user instances

    Bucket-lists and tasks will reference a user by id

    Attributes:
        id -- unique identification of user
        username -- username of user
        password_hashed -- hashed user password
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hashed = db.Column(db.String(128))
    bucketlists = db.relationship('BucketList', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not readable')

    @password.setter
    def password(self, password):
        self.password_hashed = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hashed, password)

    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return 'User <{}>'.format(self.username)


class BucketList(db.Model):
    """Class for bucket-list instances

    Tasks will reference bucket-lists by id

    Attributes:
        id -- unique identification of bucket-list
        name -- name of the bucket-list
        user_id -- id of the user that owns the bucket-list
    """
    __tablename__ = 'bucketlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tasks = db.relationship('Task', backref='bucketlist', lazy='dynamic')


class Task(db.Model):
    """Class for task instances

    Attributes:
        id -- unique identification of bucket-list
        description -- description of the user task
        user_id -- id of user that owns the task
        bucketlist_id -- id of bucket-list that the task belongs to
        """
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bucketlist_id = db.Column(db.Integer, db.ForeignKey('bucketlists.id'))

######## SCHEMAS ########
# These are classes that will help in serializing db models,
# deserializing and validating incoming json data

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(load_only=True, required=True)
    bucketlist = fields.Nested('BucketListSchema', many=True, exclude=('tasks',))


class BucketListSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    tasks = fields.Nested('TaskSchema', many=True, dump_only=True)


class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    description = fields.Str(required=True)
