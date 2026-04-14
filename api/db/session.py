import sqlite3
import os
from pathlib import Path

# Path to the db file created by init_db.py
DB_PATH = Path(__file__).resolve().parents[2] / "risk_assessment.db"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    """Dependency to get DB session."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    try:
        yield conn
    finally:
        conn.close()

