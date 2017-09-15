import os

from flask_migrate import Migrate

from bucky import create_app, db
from bucky.models import User

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User)
