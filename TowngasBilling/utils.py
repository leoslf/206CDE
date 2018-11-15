import sys
import os
import traceback
import json
from smtpd import *
import asyncore
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from flask import *

from TowngasBilling.db_connection import *

# helper functions
def rootpath(path=""):
    return os.path.dirname(os.path.abspath(__file__)) + "/" + path

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

class SMTPDaemon(SMTPServer):
    def __init__(self, localaddr, remoteaddr=(None, None)):
        SMTPServer.__init__(self, localaddr, remoteaddr)
    def process_message(self, peer, mailfrom, rcpttos, data):
        info("New Email Recieved: %s" % data)

    @staticmethod
    def run(host="localhost", port=25):
        daemon = SMTPDaemon((host, port))
        try:
            asyncore.loop(timeout=2)
        except KeyboardInterrupt:
            daemon.close()

def account_number_format(account_number):
    s = "%010d" % int(account_number if account_number else 0)
    return "-".join(map(str, [s[i:i+4] for i in range(0, len(s), 4)]))
