"""
Export every table in the SQLite database to CSV files for Power BI.

Run from the project root:
    python src/export_csv.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/qa_lab.db")
OUT_DIR = Path("data/csv")
OUT_DIR.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB_PATH) as conn:
    # sqlite_master is SQLite's own catalog: it lists every table in the file
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type = 'table'", conn
    )["name"]

    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        df.to_csv(OUT_DIR / f"{table}.csv", index=False, encoding="utf-8")
        print(f"  {table:<12} {len(df):>9,} rows")

print(f"CSV files saved in {OUT_DIR}/")
