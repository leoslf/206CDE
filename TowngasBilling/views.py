#!/usr/bin/env python

import sys
import os
import traceback
from flask import *
from jinja2 import TemplateNotFound
from TowngasBilling import app as application
from TowngasBilling.utils import *

@application.before_request
def before_request():
    g.python_version = sys.version_info[0]
    g.app_name = "TowngasBilling"
    g.authentication = authentication
    g.OrderedDict_column = OrderedDict_column

# matching route and handler
@application.route("/", defaults={"filename": "index.html"})
@application.route("/<path:filename>", methods = ["GET", "POST"])
def display(filename):
    try:
        return render_template(filename)
    except TemplateNotFound:
        return application.send_static_file(filename)

@application.route("/settings")
def settings():
    return render_template("settings.html")

@application.route("/login", methods = ["POST", "GET"])
def login():
    # Login Already 
    if logged_in():
        return redirect("/")

    if request.method == "POST":
        # login form submitted
        result = None
        try:
            results = query("staff", "username", "username='%s' AND password='%s'" % (request.form["username"], request.form["password"]))
            info(results)

            # login successful
            if len(results) == 1: 
                session["username"] = request.form["username"]
                session["displayed_username"] = request.form["username"]
                return redirect(request.referrer)

            if len(results) == 0:
                msg = "Invalid username or password"
            else:
                msg = "Login Error (DB), returned number of rows > 1"
            msg += str(results)

        except:
            tb = traceback.format_exc()
            application.logger.error("Exception in login: " + str(tb))
            msg = "Exception occured during login query: " + str(tb)

        return errmsg(msg, "login.html")

    # before login
    # GET Request
    return render_template("login.html")

@application.route("/logout")
def logout():
    # remove cookie variable
    for x in ("username", "displayed_username"):
        session.pop(x, None)
    return set_msg(dict(info="raised error"), request.referrer, redirect)

@application.route("/raise_error", methods=["POST"])
def raise_error():
    if request.method == "POST":
        assert ("msg" in request.form)
        error(request.form["msg"])
        return set_msg(dict(info="fired errmsg: %s" % request.form["msg"]), request.referrer, redirect)

@application.route("/update_table", methods=["POST", "GET"])
def update_table():
    if request.method == "POST":
        msg = dict(success="", info="", warn="", err="")
        updated_rows = 0
        inserted_rows = 0
        debug("referrer: " + request.referrer)
        try:
            table_name = request.form["table_name"]
            debug("UPDATE: " + table_name)
            debug(str(request.form))

            for name in request.form:
                err_msg = []
                # update row
                if name.startswith("id-"):
                    row_id = name.split("-")[1]
                    delta_dict = json.loads(request.form[name])
                    # msg += "update: %s, %r" % (name, delta_dict) + "<br />"
                    rc = update(table_name,
                                delta_dict,
                                condition="id = %s" % row_id,
                                errmsg=err_msg)
                    if rc < 0:
                        msg["err"] += "update failed, id: %s, delta_dict: %s" % (row_id, str(delta_dict)) + "<br />" \
                                        + err_msg[0] + "<br />"
                    else:
                        updated_rows += rc

                elif name.startswith("newrow-"):
                    delta_dict = json.loads(request.form[name])
                    msg["info"] += "insert: %s, %s" % (str(name), str(delta_dict)) + "<br />"
                    rc = insert(table_name,
                                values = delta_dict,
                                errmsg = err_msg)
                    if rc < 0:
                        msg["err"] += "update failed, delta_dict: %r" % delta_dict + "<br />" \
                                        + err_msg[0] + "<br />"
                    else:
                        msg["info"] += "inserted row's id: %d" % rc
                        inserted_rows += 1

            if updated_rows > 0:
                msg["success"] += "updated_rows: %d" % updated_rows + "<br />"
            if inserted_rows > 0:
                msg["success"] += "inserted_rows: %d" % inserted_rows + "<br />"

        except Exception as e:
            # application.logger.error("Exception in login: " + str(e))
            exception_msg = str(e)
            msg["err"] += exception_msg
            error(exception_msg)

        return set_msg(msg, request.referrer, redirect)
    return redirect(request.referrer)
