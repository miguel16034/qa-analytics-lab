"""Run a .sql file against the project database and print the result.

Usage:
    python src/run_query.py sql/01_overview.sql
"""
import sqlite3
import sys

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

sql_file = sys.argv[1]                      # the file name you pass in the terminal
query = open(sql_file, encoding="utf-8").read()

with sqlite3.connect("data/qa_lab.db") as conn:
    result = pd.read_sql(query, conn)       # runs the SQL, returns a table

print(result.to_string(index=False))