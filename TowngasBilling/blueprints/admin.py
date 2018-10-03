from flask import *
from jinja2 import TemplateNotFound
from TowngasBilling.utils import *
from collections import OrderedDict

admin = Blueprint("admin", __name__,
                  template_folder=rootpath("templates/admin"),
                  static_folder="static",
                  url_prefix="/admin")

@admin.route("/", defaults={"page": "index.html"})
@admin.route("/<page>")
def display(page):
    try:
        if logged_in() == False:
            return errmsg("Please login first")

        msg = []
        if authentication(msg):
            return render_template(admin.url_prefix + "/" + page)
        else:
            assert (len(msg) > 0)
            return errmsg(msg[0]) 
            

    except TemplateNotFound:
        return admin.send_static_file(page)

    abort(404)

