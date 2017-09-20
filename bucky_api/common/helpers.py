from flask import current_app, url_for, g

from bucky_api.models import BucketList, BucketListSchema


class BucketListPaginator(object):
    """
    Helper class to handle pagination of bucket-lists

    Attributes:
        request -- request object containing info on page number
        resource_endpoint -- name of the bucket-list collection endpoint
        resource_name -- name bucket-list array that will be sent in response
        schema -- model schema to use in serializing objects
        results_per_page -- how many bucket-lists to send in response
    """

    def __init__(self,
                 request,
                 resource_endpoint='bucketlists.bucketlists',
                 resource_name='bucket-lists',
                 schema=BucketListSchema(many=True)):
        self.request = request
        self.resource_endpoint = resource_endpoint
        self.resource_name = resource_name
        self.schema = schema
        self.results_per_page = current_app.config['BUCKETS_PER_PAGE']

    def paginate_query(self):
        """
        Make db bucket-list paginated query

        :return: dict object of json paginated response
        :rtype: dict
        """
        # default to page 1 if none is specified
        page = self.request.args.get('page', 1, type=int)
        pagination = BucketList.query.filter_by(user=g.current_user).paginate(
            page,
            per_page=self.results_per_page,
            error_out=False)
        bucketlists = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for(self.resource_endpoint, page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for(self.resource_endpoint, page=page + 1, _external=True)

        dumped_objects = self.schema.dump(bucketlists).data
        return {
            self.resource_name: dumped_objects,
            "prev": prev,
            'next': next,
            'count': pagination.total
        }
