from functools import wraps

from flask import g, request, Blueprint, make_response
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api
from sqlalchemy.exc import SQLAlchemyError
from bucky_api import db

from bucky_api.common import status
from bucky_api.models import User, UserSchema

# CREATE BLUEPRINT
auth_bp = Blueprint('auth', __name__)
auth_api = Api(auth_bp)


# CUSTOM HTTP BASIC AUTH CLASS
class CustomHTTPBasicAuth(HTTPBasicAuth):
    def error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            res = make_response(res)
            if res.status_code == 200:
                # if user didn't set status code, use 401
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys():
                res.headers['WWW-Authenticate'] = 'xBasic realm="Access to the bucky"'
            return res

        self.auth_error_callback = decorated
        return decorated


# SETUP AUTHENTICATION RESOURCE
auth = CustomHTTPBasicAuth()


@auth.verify_password
def verify_credentials(username_or_token, password):
    """callback func to be used by resources that need authentication"""
    if not username_or_token:
        # impossible to verify
        print("impossible to verify")
        return False
    if not password:
        # using token
        g.current_user = User.verify_auth_token(username_or_token)
        g.token_used = True
        print("token was used")
        return g.current_user is not None
        # using username and password
    user = User.query.filter_by(username=username_or_token).first()
    print("got user :", user)
    if user and user.verify_password(password):
        g.current_user = user
        g.token_used = False
        print("user was verified")
        return True
    print("wrong credentials")
    return False


class AuthRequiredResource(Resource):
    """Class to be inherited by resources that need user verification"""
    method_decorators = [auth.login_required]


# TOKEN AUTHENTICATION RESOURCE
class TokenResource(AuthRequiredResource):
    """Resource for issuing tokens"""

    def get(self):
        if g.token_used:
            return {"message": "Invalid credentials"}, status.HTTP_401_UNAUTHORIZED
        token = g.current_user.generate_auth_token(expiration=3600)
        return {'token': token.decode('ascii'),
                'expiration': 3600}


# INDIVIDUAL USER RESOURCE
user_schema = UserSchema()


class UserResource(AuthRequiredResource):
    """Individual user resource endpoint"""

    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {"message": "User does not exist"}, status.HTTP_404_NOT_FOUND
        # serialize user object
        result = user_schema.dump(user)
        return result.data

    def patch(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {"message": "User does not exist"}, status.HTTP_404_NOT_FOUND

        if g.current_user.id != user_id:
            # cannot change someone else's details
            return {"message": "Forbidden"}, status.HTTP_403_FORBIDDEN

        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, status.HTTP_400_BAD_REQUEST

        # Validate and deserialize input
        data, errors = user_schema.load(json_data)
        if errors:
            return errors, status.HTTP_422_UNPROCESSABLE_ENTITY

        # patch user object
        # only password can be changed for this app
        user.password = data['password']

        try:
            db.session.add(user)
            db.session.commit()
            # serialize user object
            result = user_schema.dump(user)
            return result.data

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Failed to patch",
                    "error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


# USER COLLECTION RESOURCE
class UserCollectionResource(Resource):
    """User collection endpoint"""

    def post(self):
        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, status.HTTP_400_BAD_REQUEST

        # validate and deserialize input
        data, errors = user_schema.load(json_data)
        print(data)
        print(errors)
        if errors:
            return errors, status.HTTP_422_UNPROCESSABLE_ENTITY

        # check if user already exists
        user = User.query.filter_by(username=data['username']).first()
        if user:
            return {"message": "This username already exist"}, status.HTTP_409_CONFLICT

        # create user
        user = User(username=data['username'],
                    password=data['password'])

        try:
            db.session.add(user)
            db.session.commit()
            # serialize user object
            result = user_schema.dump(User.query.get(user.id))
            return {"message": "User registered",
                    "user": result.data}, status.HTTP_201_CREATED

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Failed to create",
                    "error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


auth_api.add_resource(TokenResource, '/auth/get_token/', endpoint='token')
auth_api.add_resource(UserResource, '/auth/users/<int:user_id>', endpoint='user')
auth_api.add_resource(UserCollectionResource, '/auth/users/', endpoint='users')
