import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'xGA45@f1'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BUCKETS_PER_PAGE = 3

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL')
    DEBUG = True


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
