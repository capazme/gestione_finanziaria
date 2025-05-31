import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Singleton per la connessione globale
_connection = None

def get_connection(db_path=None):
    """
    Restituisce una connessione SQLite pronta all'uso (singleton).
    Abilita foreign keys e row_factory.
    """
    global _connection
    if _connection is None:
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "database.db")
        _connection = sqlite3.connect(db_path, check_same_thread=False)
        _connection.execute("PRAGMA foreign_keys = ON")
        _connection.row_factory = sqlite3.Row
    return _connection

@contextmanager
def db_cursor():
    """
    Context manager per ottenere un cursore e gestire commit/rollback.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

def close_connection():
    """
    Chiude la connessione globale se aperta.
    """
    global _connection
    if _connection:
        _connection.close()
        _connection = None
