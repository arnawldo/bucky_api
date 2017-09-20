from flask import request, jsonify, Blueprint, g
from flask_restful import Api
from sqlalchemy.exc import SQLAlchemyError

from bucky_api import db
from bucky_api.resources.auth import AuthRequiredResource
from bucky_api.common import status
from bucky_api.models import BucketList, Task, TaskSchema

# CREATE BLUEPRINT
tasks_bp = Blueprint('tasks', __name__)
task_api = Api(tasks_bp)

# INDIVIDUAL TASK RESOURCE
task_schema = TaskSchema()


class TaskResource(AuthRequiredResource):
    """
    Individual task endpoint

    Methods:
        patch -- change description of a single task of unique id and bucket-list id
        delete -- delete a task by id and bucket-list id
    """

    def patch(self, bucket_id, task_id):
        task = Task.query.filter_by(id=task_id,
                                    bucketlist_id=bucket_id,
                                    user=g.current_user).first()

        if not task:
            return {"message": "Task does not exist"}, status.HTTP_404_NOT_FOUND

        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, status.HTTP_400_BAD_REQUEST

        # Validate and deserialize input
        data, errors = task_schema.load(json_data)
        if errors:
            return errors, status.HTTP_422_UNPROCESSABLE_ENTITY

        # patch task object
        task.description = data['description']

        try:
            db.session.add(task)
            db.session.commit()
            # serialize task object
            result = task_schema.dump(Task.query.get(task.id))
            return {"message": "Task modified",
                    "task": result.data}

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Failed to patch",
                    "error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR

    def delete(self, bucket_id, task_id):
        task = Task.query.filter_by(id=task_id,
                                    bucketlist_id=bucket_id,
                                    user=g.current_user).first()

        if not task:
            return {"message": "Task does not exist"}, status.HTTP_404_NOT_FOUND

        try:
            db.session.delete(task)
            db.session.commit()
            return {"message": "Task deleted"}

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Failed to delete",
                    "error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


# TASK COLLECTION RESOURCE
tasks_schema = TaskSchema(many=True)


class TaskCollectionResource(AuthRequiredResource):
    def get(self, bucket_id):
        bucketlist = BucketList.query.filter_by(id=bucket_id,
                                                user=g.current_user).first()
        if not bucketlist:
            return {"message": "This bucket-list does not exist"}, status.HTTP_404_NOT_FOUND

        tasks = Task.query.filter_by(bucketlist_id=bucket_id,
                                     user=g.current_user).all()
        if not tasks:
            return {"message": "No tasks found"}, status.HTTP_404_NOT_FOUND

        # serialize queryset
        result = tasks_schema.dump(tasks)
        return {"tasks": result.data}

    def post(self, bucket_id):
        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, status.HTTP_400_BAD_REQUEST

        # validate and deserialize input
        data, errors = task_schema.load(json_data)
        if errors:
            return errors, status.HTTP_422_UNPROCESSABLE_ENTITY

        # check if bucket-list exists
        bucketlist = BucketList.query.filter_by(id=bucket_id,
                                                user=g.current_user).first()
        if not bucketlist:
            return {"message": "This bucket-list does not exist"}, status.HTTP_404_NOT_FOUND

        # check if task already exists
        task = Task.query.filter_by(description=data['description'],
                                    bucketlist=bucketlist).first()
        if task:
            return {"message": "This task already exists"}, status.HTTP_409_CONFLICT

        # create task
        task = Task(description=data['description'],
                    bucketlist=bucketlist,
                    user=g.current_user)

        try:
            db.session.add(task)
            db.session.commit()
            # serialize task object
            result = task_schema.dump(Task.query.get(task.id))
            return {"message": "Task created",
                    "task": result.data}, status.HTTP_201_CREATED

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Failed to create",
                    "error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR


task_api.add_resource(TaskResource, '/bucketlists/<int:bucket_id>/tasks/<int:task_id>', endpoint='task')
task_api.add_resource(TaskCollectionResource, '/bucketlists/<int:bucket_id>/tasks/', endpoint='tasks')
