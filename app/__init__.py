import logging

from flask import Flask
from flask_caching import Cache
from flask_appbuilder import AppBuilder, SQLA
from flask_appbuilder.menu import Menu

from app.index import CustomIndexView


"""
 Logging configuration
"""
logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)


app = Flask(__name__)
app.config.from_object("config")
cache = Cache(app, config={"CACHE_TYPE": "simple"})
db = SQLA(app)
appbuilder = AppBuilder(
    app, db.session, indexview=CustomIndexView, menu=Menu(reverse=False)
)

from . import views  # noqa
