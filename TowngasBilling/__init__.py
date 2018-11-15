import os

from flask import Flask
from TowngasBilling.config import *
from TowngasBilling.db_connection import *
from TowngasBilling.utils import *
from TowngasBilling.blueprints.admin import admin
from TowngasBilling.blueprints.settings import settings

# instantiate a Flask object
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(settings, url_prefix="/settings")
app.secret_key = "KEY"
# enable these functions in templates
app.jinja_env.globals.update(zip=zip, list=list, str=str, query=query, isinstance=isinstance, account_number_format=account_number_format)
app.jinja_env.add_extension('jinja2.ext.do')
# Trim Empty Lines
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


# Circular import 
from TowngasBilling import views, models
