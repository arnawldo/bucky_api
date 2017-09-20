from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    from bucky_api.resources.auth import auth_bp
    from bucky_api.resources.bucketlist import bucketlists_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1.0')
    app.register_blueprint(bucketlists_bp, url_prefix='/api/v1.0')

    return app
