from src.database.connection import db_cursor, get_connection
from pathlib import Path
import os

# Esempio: lista hardcoded di migrazioni (in produzione meglio file separati)
MIGRATIONS = [
    # (version, sql, description)
    (1, None, "Schema iniziale con tabelle base e viste"),
    # Aggiungi qui tuple (version, sql, description) per nuove migrazioni
]

def get_current_schema_version():
    """
    Ritorna la versione attuale dello schema dal database.
    """
    with db_cursor() as cursor:
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

def apply_migration(version, sql, description):
    """
    Applica una singola migrazione e aggiorna la tabella schema_version.
    """
    if sql:
        with db_cursor() as cursor:
            cursor.executescript(sql)
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
            (version, description)
        )

def migrate_to_latest():
    """
    Applica tutte le migrazioni mancanti.
    """
    current = get_current_schema_version()
    for version, sql, description in MIGRATIONS:
        if version > current:
            print(f"Applico migrazione {version}: {description}")
            apply_migration(version, sql, description)
    print("Schema aggiornato all'ultima versione.")

def list_migrations():
    """
    Mostra lo stato delle migrazioni applicate.
    """
    with db_cursor() as cursor:
        cursor.execute("SELECT version, applied_at, description FROM schema_version ORDER BY version")
        rows = cursor.fetchall()
        if not rows:
            print("Nessuna migrazione applicata.")
        else:
            print("Migrazioni applicate:")
            for row in rows:
                print(f"  Versione {row['version']} - {row['applied_at']}: {row['description']}")
