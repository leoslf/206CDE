from flask import *
from jinja2 import TemplateNotFound
from TowngasBilling.utils import *
from collections import OrderedDict

settings = Blueprint("settings", __name__,
                  template_folder=rootpath("templates/settings"),
                  static_folder="static",
                  url_prefix="/settings")

@settings.route("/", defaults={"page": "index.html"})
@settings.route("/<page>")
def display(page):
    try:
        if logged_in() == False:
            return errmsg("Please login first")
        return render_template(settings.url_prefix + "/" + page)

    except TemplateNotFound:
        return settings.send_static_file(page)

    abort(404)

