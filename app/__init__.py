import logging

from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from flask_appbuilder.menu import Menu

from app.index import CustomIndexView

db = SQLA()
appbuilder = AppBuilder(indexview=CustomIndexView, menu=Menu(reverse=False))


def init_app():
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s"
    )
    logging.getLogger().setLevel(logging.DEBUG)
    app = Flask(__name__)
    app.config.from_object("config")

    with app.app_context():
        db.init_app(app)
        appbuilder.init_app(app, db.session)

        from . import views  # noqa

        from .dashboard import init_dashboards  # noqa

        init_dashboards(app, db)

        return app
