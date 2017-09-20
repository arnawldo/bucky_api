from flask import request, Blueprint, g
from flask_restful import Api
from sqlalchemy.exc import SQLAlchemyError

from bucky_api import db
from bucky_api.common.helpers import BucketListPaginator
from bucky_api.models import BucketListSchema, BucketList
from bucky_api.common import status
from bucky_api.resources.auth import AuthRequiredResource

# REGISTER BLUEPRINT
bucketlists_bp = Blueprint('bucketlists', __name__)
bucket_api = Api(bucketlists_bp)

# INDIVIDUAL BUCKETLIST RESOURCE
bucketlist_schema = BucketListSchema()


class BucketListResource(AuthRequiredResource):
    """
    Individual bucket-list endpoint
    
    Methods:
        get -- get a bucket-list by id
        patch -- change the name of a single bucket-list of unique id
        delete -- delete a bucket-list by id
    """

    def get(self, bucket_id):
        bucketlist = BucketList.query.filter_by(user=g.current_user, id=bucket_id).first()
        if not bucketlist:
            return {"message": "Bucket-list not found"}, status.HTTP_404_NOT_FOUND
        result = bucketlist_schema.dump(bucketlist)
        return result.data

    def patch(self, bucket_id):
        bucketlist = BucketList.query.filter_by(id=bucket_id, user=g.current_user).first()
        if not bucketlist:
            return {"message": "Bucket-list not found"}, status.HTTP_404_NOT_FOUND

        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, status.HTTP_400_BAD_REQUEST

        # Validate and deserialize input
        data, errors = bucketlist_schema.load(json_data)
        if errors:
            return errors, status.HTTP_422_UNPROCESSABLE_ENTITY

        # patch bucket-list object
        bucketlist.name = data['name']

        try:
            db.session.add(bucketlist)
            db.session.commit()
            # serialize bucket-list object
            result = bucketlist_schema.dump(BucketList.query.get(bucketlist.id))
            return {"message": "Bucket-list modified",
                    "Bucket-list": result.data}

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Failed to patch",
                    "error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR

    def delete(self, bucket_id):
        bucketlist = BucketList.query.filter_by(id=bucket_id, user=g.current_user).first()
        if not bucketlist:
            return {"message": "Bucket-list does not exist"}, status.HTTP_404_NOT_FOUND

        try:
            db.session.delete(bucketlist)
            db.session.commit()
            return {"message": "Deleted bucket-list"}

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


# BUCKET-LIST COLLECTION RESOURCE
bucketlists_schema = BucketListSchema(many=True)


class BucketListCollectionResource(AuthRequiredResource):
    """
    Collection endpoint for bucket-lists
    
    Methods:
        get -- get all bucket-lists of current user
        post -- create a new bucket-list
    """

    def get(self):
        bucketlist_paginator = BucketListPaginator(request)
        result = bucketlist_paginator.paginate_query()
        return result

    def post(self):
        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, status.HTTP_400_BAD_REQUEST

        # validate and deserialize input
        data, errors = bucketlist_schema.load(json_data)
        if errors:
            return errors, status.HTTP_422_UNPROCESSABLE_ENTITY

        # check if bucket-list already exists
        bucketlist = BucketList.query.filter_by(name=data['name'], user=g.current_user).first()
        if bucketlist:
            return {"message": "Bucket-list already exists"}, status.HTTP_409_CONFLICT

        # create new bucketlist
        bucketlist = BucketList(name=data['name'], user=g.current_user)

        try:
            db.session.add(bucketlist)
            db.session.commit()
            return {"message": "Created bucket-list"}, status.HTTP_201_CREATED

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


bucket_api.add_resource(BucketListResource, '/bucketlists/<int:bucket_id>', endpoint='bucketlist')
bucket_api.add_resource(BucketListCollectionResource, '/bucketlists/', endpoint='bucketlists')
