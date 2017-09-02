# Copyright 2017 Michael J Simms

import os
import sqlite3


class Database(object):
    """Base class for a database. Encapsulates common functionality."""
    db_file = ""
    log_file_name = ""

    def __init__(self, root_dir):
        self.log_file_name = os.path.join(root_dir, 'database.log')
        super(Database, self).__init__()

    def log_error(self, log_str):
        with open(self.log_file_name, 'a') as f:
            f.write(str(log_str) + "\n")
            f.close()

    def is_quoted(self, s):
        if len(s) < 2:
            return False
        return s[0] == '\"' and s[len(s)-1] == '\"'

    def quote_identifier(self, s, errors="strict"):
        if self.is_quoted(s):
            return s
        encodable = s.encode("utf-8", errors).decode("utf-8")
        null_index = encodable.find("\x00")
        if null_index >= 0:
            return ""
        return "\"" + encodable.replace("\"", "\"\"") + "\""


class SqliteDatabase(Database):
    """Abstract Sqlite database implementation."""
    def __init__(self, root_dir):
        Database.__init__(self, root_dir)

    def connect(self):
        pass

    def execute(self, sql):
        try:
            con = sqlite3.connect(self.db_file)
            with con:
                cur = con.cursor()
                cur.execute(sql)
                return cur.fetchall()
        except:
            self.log_error("Database error:\n\tfile = " + self.db_file + "\n\tsql = " + self.quote_identifier(sql))
        finally:
            if con:
                con.close()
        return None
