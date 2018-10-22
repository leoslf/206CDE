#!/usr/bin/env python

import sys
import os
import traceback
import json
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

@application.route("/check_for_record")
def check_for_record():
    if not logged_in():
        return jsonify(result=False)

    table = request.args.get("table")
    values_json = request.args.get("values")
    values = json.loads(values_json)

    results = query(table, condition = " AND ".join(["%s = '%s'" % (key, values[key]) for key in values]))

    # return jsonify(result=(len(query(table, filters=values)) > 0))
    return jsonify(results=len(results) > 0)
    

@application.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        # Registration form submitted
        login_keys = ["username", "password"]
        customer_keys = ["given_name", "last_name", "HKID", "email"]
        premise_keys = ["address"]

        if not all(key in request.form for key in login_keys + customer_keys + premise_keys):
            return errmsg("not all of the fields exist in request.form", request.referrer)

        login = { key: request.form[key] for key in login_keys }
        customer = { key: request.form[key] for key in customer_keys }
        premise = { key: request.form[key] for key in premise_keys }

        rc = -1
        msg = []

        connection = database_connection(autocommit=False)
        try:
            # insert if premise not exist
            results = query("premise", condition="address = '%s'" % premise["address"], err_msg=msg, connection=connection)
            if results is None:
                return errmsg("Failed to query from premise, " + ", ".join(msg), request.referrer)
                
            if len(results) == 0:
                # create record for premise
                premise_id = insert("premise", values=premise, err_msg=msg, connection=connection)
                if premise_id < 0:
                    return errmsg("Failed to insert into premise: " + ", ".join(msg), request.referrer)
            else:
                premise_id = results[0]["id"]
                if len(results) > 1:
                    error("Unique constraint violated!")

            # recieved premise_id

            # create customer
            customer_id = insert("customer", values=customer, err_msg=msg, connection=connection)
            if customer_id < 0:
                return errmsg("Failed to insert into customer, " + ", ".join(msg), request.referrer)
            
            # Place customer_id as foreign key of Login
            login["customer_id"] = customer_id

            # create login
            login_id = insert("login", values=login, err_msg=msg, connection=connection)
            if login_id < 0:
                return errmsg("Failed to insert into login, " + ", ".join(msg), request.referrer)

            # create account
            account = {
                    "customer_id": customer_id,
                    "premise_id": premise_id
            }

            account_id = insert("account", values=account, err_msg=msg, connection=connection)
            if account_id < 0:
                return errmsg("Failed to insert into account, " + ", ".join(msg), request.referrer)

            connection.commit()
        finally:
            connection.close()

    # GET Request
    if logged_in():
        return redirect("/")
    return render_template("register.html")

@application.route("/login", methods = ["POST", "GET"])
def login():
    # Login Already 
    if logged_in():
        return redirect("/")

    if request.method == "POST":
        # login form submitted
        try:
            username, password = (request.form[key] for key in ("username", "password"))
        except Exception as e:
            return errmsg(str(e), request.referrer)

        result = None
        try:
            results = query("login l", "l.username, c.id AS customer_id, (c.given_name || ' ' || c.last_name) AS display_name", condition="username = '%s' AND password = '%s'" % (username, password), join="LEFT OUTER JOIN customer c ON c.id = l.customer_id")
            info("login query results: '%r'" % results)

            # login successful
            if len(results) == 1: 
                results = results[0]
                session["username"] = username
                session["display_name"] = username if results["customer_id"] is None else results["display_name"]
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
    try:
        for x in ("username", "display_name"):
            session.pop(x, None)
        return redirect("/")
    except Exception as e:
        return errmsg("Exception: " + str(e), request.referrer, redirect)

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
