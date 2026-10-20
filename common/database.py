# Small helper for opening the shared SQLite database
# Omar Tabsh - 202400798

import os
import sqlite3
from contextlib import contextmanager


@contextmanager
def connect(db_path):
    """Open a connection, commit if the block succeeds, roll back if it fails, always close."""
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
