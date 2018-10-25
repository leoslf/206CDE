from collections import OrderedDict
import cx_Oracle
import traceback
from TowngasBilling.debug import *

credential = {
        "user": "G3_team001",
        "password": "admin123",
        "dsn": "144.214.177.102",
}

def database_connection(autocommit=True):
    """Get Database Connection"""
    conn = None
    try:
        conn = cx_Oracle.connect(**credential)
        conn.autocommit = autocommit
    except Exception as e:
        error("Cannot connect to database", str(e), str(e.args))
    return conn

def db_version():
    with database_connection() as conn:
        info(conn.version)

    return

def query(table,
          columns="*",
          condition="",
          join="",
          description=False,
          orderby=None,
          filters=None,
          err_msg=None,
          connection=None,
          *argv,
          **kwargs):
    """Queries Result Set from Database

    Args:
        table:          Name of table that exists in the database connected.
        columns:        comma seperated string or list of column names, default: "*".
        condition:      content of the WHERE clause in SQL statement (without WHERE keyword).
        join:           optional, complete * JOIN clause in SQL statement.
        description:    boolean expression that indicates whether column descriptions are requested by the caller, defaulted to False.
        orderby:        optional, column name(s) [ASC|DESC], content of ORDER BY clause in SQL statement.
        filters:        optional, alternative to screen out the content in the rows, only rows matched the key-value pairs (NOTE: key should be in lower case).
        err_msg:        optional, list to pass error message back to caller by reference.

    Returns:
        A list of OrderedDict as Result Set if successful,
        None otherwise.

    No exceptions would be raised.
    """
        

    def _rows_generator(cursor, columns):
        for row in cursor.fetchall():
            d = OrderedDict(zip(columns, row))
            if filters is None or \
                    (isinstance(filters, dict) and (len(filters) == 0 or any(col in d and d[col.lower()] == filters[col] for col in filters))):
                yield d

    if isinstance(columns, list):
        columns = ", ".join(map(str, columns))

    sql = "SELECT %s FROM %s" % (columns, table) \
            + (" " + str(join) if join != "" else "") \
            + (" WHERE " + str(condition) if condition != "" else "") \
            + (" ORDER BY " + str(orderby) if orderby is not None else "")

    debug(sql)
    if isinstance(filters, dict):
        debug("filters:", filters)

    if connection is None:
        conn = database_connection()
    else:
        conn = connection

    if conn is None:
        if isinstance(err_msg, list):
            err_msg.append("conn is None, Cannot get database connection")
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            columns = list(map(lambda s: s.lower(), list(zip(*cursor.description))[0]))
            debug("columns: '%r'" % columns)

            rows = list(_rows_generator(cursor, columns))

            if description:
                return OrderedDict([("rows", rows), ("description", cursor.description), ("columns", columns)])
            else:
                return rows

    except Exception as e:
        tb = traceback.format_exc()
        msg = "Exception: '%s', %s" % (str(e), tb)
        error("Exception in query(): ", e, tb)
        if isinstance(err_msg, list):
            err_msg.append(msg)
    finally:
        if connection is None:
            if conn is not None:
                conn.close()

    return None

def insert(table,
           columns="",
           values="",
           err_msg=None,
           connection=None,
           *argv,
           **kwargs):

    if columns == "" and isinstance(values, dict):
        columns = "(" + ", ".join(map(str, values.keys())) + ")"
        values = ", ".join(["'%s'" % values[col] for col in values.keys()])

    elif columns != "" and isinstance(values, str):
        # comma delimited string
        columns = "("+ columns +")"
    elif isinstance(values, list):
        values = ", ".join(["'%s'" % x for x in values])
    else:
        if err_msg is list:
            err_msg.append("values provided is neither dictionary with columns nor string paired with columns nor list paired with columns")
        return -1

    sql = "INSERT INTO " + table + " " \
            + columns \
            + " VALUES ("+ values +")"
    debug(sql)
    
    if connection is None:
        conn = database_connection()
    else:
        conn = connection

    try:
        with conn.cursor() as cursor:
            new_id_var = cursor.var(cx_Oracle.NUMBER)
            cursor.execute(sql  + " returning id into :new_id", {"new_id": new_id_var})
            new_id  = new_id_var.getvalue()[0]
            debug("new_id: '%r'" % new_id)
            return new_id

    except Exception as e:
        msg = "Exception: %s" % str(e)
        exception(e)
        if isinstance(err_msg, list):
            err_msg.append(msg)
    finally:
        if connection is None:
            conn.commit()
            conn.close()


    return -1

def update(table,
           values,
           condition="",
           err_msg=None,
           connection=None,
           *argv,
           **kwargs):

    col_n_val = ", ".join(["%s = '%s'" % (column, values[column]) for column in values])

    sql = "UPDATE " + table \
            + " SET " + col_n_val \
            + ((" WHERE " + condition) if condition != "" else "")

    debug(sql)
    
    if connection is None:
        conn = database_connection()
    else:
        conn = connection

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.rowcount

    except Exception as e:
        msg = "Exception: errno %r, %r" % (e.args[0], e)
        if err_msg is not None:
            err_msg.append(msg)

        debug(msg)
    finally:
        if connection is None:
            conn.commit()
            conn.close()

    return -1

def delete(table,
           condition="",
           err_msg=None,
           connection=None,
           *argv,
           **kwargs):
    
    sql = ("DELETE FROM " + table \
            + ((" WHERE " + condition) if condition != "" else ""))
    debug(sql)

    if connection is None:
        conn = database_connection()
    else:
        conn = connection

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.rowcount

    except Exception as e:
        msg = "errno %r, %r" % (e.args[0], e)
        if err_msg is not None:
            err_msg.append(msg)
    finally:
        if connection is None:
            conn.commit()
            conn.close()

    return -1
