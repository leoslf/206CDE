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
    return all(x in session for x in ("username", "displayed_username"))

def authentication(err_msg=None):
    if logged_in():
        try:
            # 2 == manager, 3 == admin
            msg = []
            print (session["username"])
            results = query("staff", condition="username = '%s' AND role >= 2" % session["username"], err_msg=msg)
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
            if err_msg is not None:
                err_msg.append("Permission Denied")

        except:
            tb = traceback.format_exc()
            error("authentication Exception: in query, username: %s : " % (session["username"] + str(tb)))
            if err_msg is not None:
                assert (isinstance(err_msg, list))
                err_msg.append(tb)
                debug(tb)
    else:
        err_msg.append("not logged in")

    
    return False

def OrderedDict_column(od, col, nonempty_filter=False):
    debug(od)
    result = [x[col] for x in od if col in x and (nonempty_filter == False or nonempty_filter == True and len(x[col]) > 0)]
    debug(result)
    return result 

def set_msg(msg_dict, page, f=render_template):
    resp = make_response(f(urlparse(str(page)).path))
    assert (isinstance(msg_dict, dict))
    for key in msg_dict:
        resp.set_cookie(key + "msg", msg_dict[key])
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
