import sqlite3
import os
import sys

from _configs import *

logfile = open(LOG_FILE,'w', 1)
sys.stdout = logfile
sys.stdin = logfile
sys.stderr = logfile

DB_DIR_PATH
os.makedirs(DB_DIR_PATH, exist_ok=True)

#-----------------------------------------
# SQLITE
#-----------------------------------------
def db_open(db_file):
    """
    Insert speed data into database table
    """
    try:
        db_conn = sqlite3.connect(db_file)
        cursor = db_conn.cursor()
    except sqlite3.Error as e:
        print("[ERROR][DB] Failed: sqlite3 Connect to DB ", db_file)
        print("[ERROR][DB] Error Msg: ", e)
        # return None
    sql_cmd = '''create table if not exists {} (id text primary key,
                 date text, 
                 hour text, 
                 minute text,
                 mean_speed text,
                 speed_units text, 
                 direction text, 
                 counter integer,
                 sd integer,
                 image_path text,
                 car_type text,
                 car_color text,
                 cam_location text)'''.format(DB_TABLE)
    try:
        db_conn.execute(sql_cmd)
    except sqlite3.Error as e:
        print("[ERROR][DB] Failed: To Create Table %s on sqlite3 DB ", DB_TABLE, db_file)
        print("[ERROR][DB] Error Msg: ", e)
        return None
    else:
        db_conn.commit()
    return db_conn

def isSQLite3(filename):
    """
    Determine if filename is in sqlite3 format
    """
    if os.path.isfile(filename):
        if os.path.getsize(filename) < 100: # SQLite database file header is 100 bytes
            size = os.path.getsize(filename)
            # logging.error("%s %d is Less than 100 bytes", filename, size)
            return False
        with open(filename, 'rb') as fd:
            header = fd.read(100)
            if header.startswith(b'SQLite format 3'):
                # logging.info("Success: File is sqlite3 Format ", filename)
                return True
            else:
                # logging.error("Failed: File NOT sqlite3 Header Format ", filename)
                return False
    else:
        # logging.warning("File Not Found ", filename)
        # logging.info("Create sqlite3 database File ", filename)
        try:
            conn = sqlite3.connect(filename)
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            # logging.error("Failed: Create Database %s.", filename)
            # logging.error("Error Msg: ", e)
            return False
        conn.commit()
        conn.close()
        # logging.info("Success: Created sqlite3 Database ", filename)
        return True

def db_check(db_file):
    """
    Check if db_file is a sqlite3 file and connect if possible
    """
    if isSQLite3(db_file):
        try:
            conn = sqlite3.connect(db_file, timeout=1)
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print("[ERROR][DB] Failed: sqlite3 Connect to DB ", db_file)
            print("Err Msg: ", e)
            return None
    else:
        print("[ERROR][DB] Failed: sqlite3 Not DB Format ", db_file)
        return None
    conn.commit()
    if CONSOLE_DEBUGGER >= 4: print("[NOTICE][DB] Success: sqlite3 Connected to DB ", db_file)
    return conn

def db_save_record(speed_data):
    try:
        sql_cmd = '''insert into {} values {}'''.format(DB_TABLE, speed_data)
        db_conn = db_check(DB_PATH)
        db_conn.execute(sql_cmd)
        db_conn.commit()
        db_conn.close()
    except sqlite3.Error as e:
        print("[ERROR][DB] Failed: To INSERT Speed Data into TABLE ", DB_TABLE)
        print("Err Msg: ", e)
    else:
        if CONSOLE_DEBUGGER >= 4: print("[NOTICE][DB] SQL - Inserted sqlite3 Data Row into ", DB_PATH)

def db_update_record(sql_cmd):
    try:
        db_conn = db_check(DB_PATH)
        db_conn.execute(sql_cmd)
        db_conn.commit()
        db_conn.close()
    except sqlite3.Error as e:
        print("[ERROR][DB] Failed: To UPDATE Speed Data into TABLE ", DB_TABLE)
        print("Err Msg: ", e)
    else:
        if CONSOLE_DEBUGGER >= 4: print("[NOTICE][DB] SQL - Updated sqlite3 Data Row into ", DB_PATH)

def db_select_record(sql_cmd):
    try:
        db_conn = db_check(DB_PATH)
        if CONSOLE_DEBUGGER >= 4: print("[SQL] " + sql_cmd.replace('\n', ' ').replace('\r', ''))
        query = db_conn.execute(sql_cmd)
        colname = [ d[0] for d in query.description ]
        result = [ dict(zip(colname, r)) for r in query.fetchall() ]
        # result = cursor.fetchall()
        db_conn.close()
    except sqlite3.Error as e:
        print("[ERROR][DB] Failed: To Select Speed Data from ", DB_TABLE)
        print("Err Msg: ", e)
    else:
        if CONSOLE_DEBUGGER >= 4: print("[NOTICE][DB] SQL - Select sqlite3 Data ", DB_PATH)
        return result


db_conn = db_check(DB_PATH)
# check and open sqlite3 db
if db_conn is not None:
  db_conn = db_open(DB_PATH)
  if db_conn is None:
      print("[ERROR][DB] Failed: Connect to sqlite3 DB ", DB_PATH)
      db_is_open = False
  else:
      if CONSOLE_DEBUGGER >= 4: print("[NOTICE][DB] sqlite3 DB is Open ", DB_PATH)
      db_cur = db_conn.cursor()  # Set cursor position
      db_is_open = True
#-----------------------------------------