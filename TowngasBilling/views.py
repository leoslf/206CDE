#!/usr/bin/env python

import sys
import os
import traceback
import json

from io import BytesIO
import barcode
import qrcode

from flask import *
from jinja2 import TemplateNotFound
from TowngasBilling import app as application
from TowngasBilling.utils import *
import TowngasBilling.utils



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

@application.route("/check_for_record", methods = ["POST"])
def check_for_record():
    # TODO: find work around to enhance security
    # if not logged_in():
    #     return jsonify(result=False)

    # table = request.args.get("table")
    # values_json = request.args.get("values")

    table = request.form["table"]
    values_json = request.form["values"]
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
                if results["customer_id"] is not None:
                    session["customer_id"] = results["customer_id"]
                    try:
                        accounts = query("account", condition = "customer_id = " + str(results["customer_id"]))
                        if len(accounts) > 0:
                            session["account_id"] = accounts[0]["id"]
                    except:
                        tb = traceback.format_exc()
                        application.logger.error("Exception in account query: " + str(tb))
                        msg = "Exception occured during account query: " + str(tb)
                        return errmsg(msg, request.referrer)
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

@application.route("/set_show_user_perspective", methods=["POST"])
def set_show_user_perspective():
    additional_data = {}
    if authentication():
        try:
            value = request.form['show_user_perspective'] == 'true'
            info("[administrator: %s] setting show_user_perspective: %r" % (session['username'], value))
            session['show_user_perspective'] = value
            additional_data['state'] = admin_showing_user_perspective()
            return jsonify(success=True, **additional_data)
        except Exception as e:
            error(str(e))
            additional_data['errmsg'] = str(e)
            return jsonify(success=False, **additional_data), 400

    return jsonify(success=False), 401

@application.route("/raise_error", methods=["POST"])
def raise_error():
    if request.method == "POST":
        assert ("msg" in request.form)
        error(request.form["msg"])
        return set_msg(dict(info="fired errmsg: %s" % request.form["msg"]), request.referrer, redirect)

@application.route("/use_account", methods=["POST"])
def use_account():
    if request.method == "POST":
        if "account_id" in request.form:
            session["account_id"] = int(request.form["account_id"])
            return jsonify(successful=True)
        error("account_id not in request.form")
        return jsonify(successful=False, msg="account_id not in request.form")

@application.route("/use_customer_id", methods=["POST"])
def use_customer_id():
    if request.method == "POST":
        if "customer_id" in request.form:
            value = int(request.form["customer_id"])
            if value == -1:
                session.pop("customer_id")
            else:
                session["customer_id"] = value 
            return jsonify(successful=True)
        error("customer_id not in request.form")
        return jsonify(successful=False, msg="customer_id not in request.form")

@application.route("/execute_sql", methods=["POST"])
def execute_sql():
    msg = ""
    try:
        if request.method == "POST":
            if len(request.form["sql"]) < 1:
                raise ValueError

            sql = request.form["sql"]

            results = {}
            cursor_results = OrderedDict()

            with database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    results['cursor_results'] = { attr: str(getattr(cursor, attr)) for attr in dir(cursor)}

                    if 'select' in sql.lower():
                        columns = list(map(lambda s: s.lower(), list(zip(*cursor.description))[0]))
                        rows = list(map(lambda row: OrderedDict(zip(columns, row)), cursor.fetchall()))
                        results['query_results'] = dict(columns=columns, rows=rows)
                        
            return jsonify(success=True, **results)
    except (KeyError, ValueError, Exception) as e:
        error(e)
        return jsonify(success=False, exception=str(e)), 400


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
                                err_msg = err_msg)
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
            exception(exception_msg)

        return set_msg(msg, request.referrer, redirect)
    return redirect(request.referrer)


def gen_code39(content, **kwargs):
    fp = BytesIO()
    makepng = barcode.writer.ImageWriter()
    writer_options = {
            "write_text": False,
            "module_height": 7.5,
            "quiet_zone": 1.5,
        }
    writer_options.update(**kwargs)
    debug(writer_options)
    # https://pythonhosted.org/pyBarcode/writers/index.html#common-writer-options
    barcode.generate(
        'code39',
        content,
        output=fp,
        writer=makepng,
        add_checksum=False,
        writer_options=writer_options,
    )
    image = fp.getvalue()
    fp.close()
    return image

@application.route("/code39/<content>")
def png_code39(content):
    response = make_response(gen_code39(content, **request.args))
    response.headers["Content-type"] = "image/png"
    return response

@application.route("/report_reading", methods=["GET"])
def report_reading_request():
    required_parameters = ("reading", "date")
    optional_parameters = ("account_id",)
    
    # parameter checking
    if not logged_in():
        return jsonify(success=False, msg="Please login first"), 401

    try:
        if all(param in request.args for param in optional_parameters):
            account_id = int(request.args.get("account_id"))
            errmsg = []
            accounts = query("Account", condition="id = %d" % account_id, err_msg=errmsg)
            if accounts is None:
                raise Exception("\n".join(map(str, errmsg)))
            if len(accounts) < 1:
                raise ValueError("Cannot find account_id: %d" % account_id)
        elif "account_id" in session:
            account_id = session["account_id"]
        else:
            raise ValueError("Please select account first")

        if not all(param in request.args for param in required_parameters):
            raise ValueError("missing parameter(s): %r" % list(param for param in required_parameters if param not in request.args))

        reading = int(request.args.get("reading"))

        date = dateformat(strptime(request.args.get("date"), format="%Y-%m-%d"), oracle=True)

    except ValueError as e:
        error(e)
        return jsonify(success=False, msg=str(e)), 400
    except Exception as e:
        error(e)
        return jsonify(success=False, msg=str(e)), 500

    # call helper function
    return report_reading(account_id, date, reading)

@application.route("/add_issue_date", methods=["POST"])
def add_issue_date():
    errmsg = []
    rc = insert("bill_issue_date", values = {"issue_date": dateformat(strptime(request.form["issue_date"], "%Y-%m-%d"))}, err_msg=errmsg)
    if rc < 0:
        return jsonify(success=False, msg = "\n".join(map(str, errmsg))), 400
    return jsonify(success=True) 

@application.route("/recieve_payment", methods=["POST"])
def recieve_payment():
    try:
        if "account_id" not in session:
            raise ValueError("Please choose account first")

        if "amount" not in request.form:
            raise ValueError("amount is missing")

        values = {
                "account_id": session["account_id"],
                "payment_date": dateformat(today(), oracle=True),
                "amount": request.form["amount"]
        }

        errmsg = []
        rc = insert("payment", values=values, err_msg=errmsg)
        if rc < 0:
            raise Exception("Error in insert, %s" % "\n".join(map(str, errmsg)))

    except ValueError as e:
        error(e)
        return jsonify(success=False, msg=str(e)), 400
    except Exception as e:
        error(e)
        return jsonify(success=False, msg=str(e)), 500

    return jsonify(success=True)

@application.route("/payment", methods=["POST"])
def payment():
    if "amount" not in request.form:
        return abort(400)

    return render_template("payment.html", amount=request.form["amount"])


