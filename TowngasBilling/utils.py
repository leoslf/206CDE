import sys
import os
from os.path import dirname, abspath

import inspect
import traceback
import json
import asyncore
import datetime
import flask

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from flask import *

from dateutil.relativedelta import *

from TowngasBilling.db_connection import *


# helper functions
def rootpath(path=""):
    return abspath(dirname(abspath(__file__)) + "/" + path)

def logged_in():
    return all(x in session for x in ("username", "display_name"))

def authentication(err_msg=None):
    if logged_in():
        try:
            # 2 == manager, 3 == admin
            msg = []
            debug("authentication, session[\"username\"]: %s" % session["username"])
            results = query("login", condition="username = '%s' AND role >= 2" % session["username"], err_msg=msg)
            # info("results: ", results)
            if results is None:
                error("results is None")
                if err_msg is not None:
                    err_msg.append("results is None")
                    if len(msg) > 0:
                        err_msg[0] += msg[0]

                    debug(err_msg[0])
                return False

            print (results)
            if len(results) == 1:
                # successful
                return True

            if isinstance(err_msg, list):
                err_msg.append("Permission Denied")

        except Exception as e:
            msg = "authentication Exception: in query, username: %s, %s" % (session["username"], str(e))
            error(msg)
            if isinstance(err_msg, list):
                err_msg.append(msg)
        finally:
            debug("err_msg: '%r'" % err_msg)
    else:
        if isinstance(err_msg, list):
            err_msg.append("not logged in")
    
    return False

def OrderedDict_column(od, col, nonempty_filter=False):
    debug(od)
    result = [x[col] for x in od if col in x and (nonempty_filter == False or nonempty_filter == True and len(x[col]) > 0)]
    debug(result)
    return result 

def set_msg(msg_dict, page, f=render_template):
    resp = make_response(f(urlparse(str(page)).path))
    if isinstance(msg_dict, dict):
        for key in msg_dict:
            resp.set_cookie(key + "msg", msg_dict[key])
    else:
        resp.set_cookie("errmsg", "set_msg failed!, isinstance(msg_dict, dict) == False: '%r'" % msg_dict)
    return resp

def errmsg(msg, page="error.html", f=render_template):
    return set_msg({'err' : msg}, page, f)

def account_number_format(account_number):
    s = "%010d" % int(account_number if account_number else 0)
    return "-".join(map(str, [s[i:i+4] for i in range(0, len(s), 4)]))

def is_bill_visible(args):
    if not logged_in():
        return False
    attributes = ('account_id', 'date')
    if args is None or not all(attribute in args for attribute in attributes):
        return False
    accounts = query("Account", condition = "account_id = %d" % int(args["account_id"]))
    if accounts is None or len(accounts) < 1:
        return False
    return True

def query_bill(args, err_msg=None):
    try:
        account_id, date = args['account_id'], args['date']
        bills = query("Bill_view", condition = "account_id = %s AND bill_date <= TO_DATE('%s', 'DD-MON-YY')" % (str(account_id), str(date)), limit=1)
        if bills is None:
            raise ValueError
        return bills
    except KeyError as e:
        error(str(e))
        if authentication():
            return query("Account_view", condition = "Account_id = -1")
        if err_msg:
            err_msg.append(str(e))
        return None
    except ValueError as e:
        error(str(e))
        if err_msg:
            err_msg.append(str(e))
        return None

def utils_export():
    return { name: obj for name, obj in inspect.getmembers(sys.modules[__name__])
                if (inspect.isfunction(obj) and name not in dir(flask)) }

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def dateformat(value, format='%d-%b-%Y', oracle=False):
    if oracle:
        format = "%d-%b-%y"
    return value.strftime(format)

def datemath(value, **kwargs):
    value = datetime.datetime.strptime(value, "%d-%b-%y")
    if len(kwargs) > 0:
        value += relativedelta(**kwargs)
    return dateformat(value)
