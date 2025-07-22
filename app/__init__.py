# app/__init__.py
from flask import Flask
from config import Config
from app.extensions import db  # ✅ updated import
from app.routes import register_routes  # your blueprints


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    register_routes(app)

    return app
