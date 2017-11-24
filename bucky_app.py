import os

from flask_cors import CORS
from flask_migrate import Migrate

from bucky_api import create_app, db
from bucky_api.models import User, BucketList, Task

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
CORS(app)
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, BucketList=BucketList, Task=Task)
