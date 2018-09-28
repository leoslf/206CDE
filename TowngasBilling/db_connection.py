from collections import OrderedDict
import cx_Oracle
import traceback
from debug import *

credential = {
        "user": "G3_team001",
        "password": "admin123",
        "dsn": "144.214.177.102",
}

def _db_conn():
    """Get Database Connection"""
    conn = None
    try:
        conn = cx_Oracle.connect(**credential)
    except Exception as e:
        error("Cannot connect to database", e.message, e.args)

    return conn

def db_version():
    with _db_conn() as conn:
        info(conn.version)

    return

def query(table,
          column="*",
          condition="",
          join="",
          description=False,
          orderby=None,
          filter=None,
          err_msg=None,
          *argv,
          **kwargs):

    def _rows_generator(cursor):
            columns = list(zip(*cursor.description))[0]
            for row in cursor.fetchall():
                yield OrderedDict(zip(columns, row))

    sql = "SELECT %s FROM %s" % (column, table) \
            + (" ORDER BY " + orderby if orderby is not None else "") \
            + (" WHERE " + condition if condition != "" else "") \
            + (" INNER JOIN " + join if join != "" else "")

    debug(sql)

    with _db_conn() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)

                rows = list(_rows_generator(cursor))

                return rows if description == False else OrderedDict([("rows", rows), ("description", cursor.description), ("columns", columns)])

        except Exception as e:
            tb = traceback.format_exc()
            error("Exception:", e, tb)
            if err_msg is not None:
                debug("err_msg is not None")
                assert (isinstance(err_msg, list))
                err_msg.append(tb)
                debug(err_msg)

    return None

def insert(table,
           columns="",
           values="",
           errmsg=None,
           *argv,
           **kwargs):

    if columns == "" and isinstance(values, dict):
        columns = "(" + ", ".join(map(str, values.keys())) + ")"
        values = ", ".join(["'%s'" % x for x in values.values()])

    elif columns != "" and isinstance(values, str):
        # comma delimited string
        columns = "("+ columns +")"
    elif isinstance(values, list):
        values = ", ".join(["'%s'" % x for x in values])
    else:
        if errmsg is list:
            errmsg.append("values provided is neither dictionary with columns nor string paired with columns nor list paired with columns")
        return -1

    sql = "INSERT INTO " + table + " " \
            + columns \
            + " VALUES ("+ values +")"
    debug(sql)

    with _db_conn() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                return cursor.lastrowid

        except Exception as e:
            msg = "Exception: errno %r, %r" % (e.args[0], e)
            if errmsg is not None:
                errmsg.append(msg)

    return -1

def update(table,
           values,
           condition="",
           errmsg=None,
           *argv,
           **kwargs):

    col_n_val = ", ".join(["%s = '%s'" % (column, values[column]) for column in values])

    sql = "UPDATE " + table \
            + " SET " + col_n_val \
            + ((" WHERE " + condition) if condition != "" else "")

    debug(sql)
    
    with _db_conn() as conn:

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            msg = "Exception: errno %r, %r" % (e.args[0], e)
            if errmsg is not None:
                errmsg.append(msg)

            debug(msg)

    return -1

def delete(table,
           condition="",
           errmsg=None,
           *argv,
           **kwargs):
    
    sql = ("DELETE FROM " + table \
            + ((" WHERE " + condition) if condition != "" else ""))
    debug(sql)
    
    with _db_conn() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            msg = "MYSQLError: errno %r, %r" % (e.args[0], e)
            if errmsg is not None:
                errmsg.append(msg)

    return -1
