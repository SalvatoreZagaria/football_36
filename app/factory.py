import logging
import flask

from app import app_config

logger = logging.getLogger()


def create_app(service_name, dev=True):
    flask_app = flask.Flask(__name__)

    init_config(flask_app.config)
    configure_database(flask_app)
    configure_node4j()

    from app.routes import game, entities
    flask_app.register_blueprint(game.bp)
    flask_app.register_blueprint(entities.bp)

    @flask_app.after_request
    def add_headers(response):
        response.headers.add('Content-Type', 'application/json')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'PUT, GET, POST, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Expose-Headers',
                             'Content-Type,Content-Length,Authorization,X-Pagination')
        return response

    return flask_app


def init_config(config):
    config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    url = app_config.get_database_url()
    config['DB_VENDOR'] = 'postgres'
    config['SQLALCHEMY_DATABASE_URI'] = url
    config['DATABASE_URI'] = url


def configure_database(flask_app):
    from app.model import db
    db.init_app(flask_app)


def configure_node4j():
    from app.utils import neo4j_client
