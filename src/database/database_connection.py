"""
Modulo per la gestione della connessione al database SQLite.

Fornisce un connection manager thread-safe e funzioni utility
per l'inizializzazione e gestione del database.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import json


class DatabaseConfig:
    """Configurazione per il database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inizializza la configurazione del database.
        
        Args:
            db_path: Percorso del file database. Se None, usa il default.
        """
        if db_path is None:
            # Crea directory data se non esiste
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "database.db")
        else:
            self.db_path = db_path
        
        self.schema_file = Path(__file__).parent / "schema.sql"
        
        # Configurazione SQLite
        self.timeout = 30.0  # timeout per lock del database
        self.isolation_level = None  # autocommit disabilitato
        
        # Setup logging
        self.logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Gestisce la connessione al database SQLite."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Inizializza il gestore della connessione.
        
        Args:
            config: Configurazione del database. Se None, usa default.
        """
        self.config = config or DatabaseConfig()
        self._connection: Optional[sqlite3.Connection] = None
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Ottiene una connessione al database.
        
        Returns:
            Connessione SQLite attiva
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.config.db_path,
                timeout=self.config.timeout,
                isolation_level=self.config.isolation_level,
                check_same_thread=False
            )
            
            # Abilita foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
            
            # Imposta row factory per risultati come dizionari
            self._connection.row_factory = sqlite3.Row
            
            self.config.logger.info(f"Connessione database aperta: {self.config.db_path}")
        
        return self._connection
    
    def close(self):
        """Chiude la connessione al database se aperta."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self.config.logger.info("Connessione database chiusa")
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_connection()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.get_connection().commit()
        else:
            self.get_connection().rollback()
            self.config.logger.error(f"Transazione rollback per errore: {exc_val}")


# Singleton per connessione globale
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """
    Ottiene l'istanza singleton della connessione database.
    
    Returns:
        DatabaseConnection singleton
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


@contextmanager
def get_db_cursor():
    """
    Context manager per ottenere un cursore database.
    
    Yields:
        Cursore SQLite per eseguire query
    """
    conn = get_db_connection()
    cursor = conn.get_connection().cursor()
    try:
        yield cursor
        conn.get_connection().commit()
    except Exception as e:
        conn.get_connection().rollback()
        logging.error(f"Errore database: {e}")
        raise
    finally:
        cursor.close()


def init_database(force_recreate: bool = False):
    """
    Inizializza il database creando le tabelle dallo schema.
    
    Args:
        force_recreate: Se True, ricrea il database da zero
    """
    config = DatabaseConfig()
    
    # Se force_recreate, elimina il database esistente
    if force_recreate and os.path.exists(config.db_path):
        os.remove(config.db_path)
        config.logger.warning(f"Database eliminato: {config.db_path}")
    
    # Leggi lo schema SQL
    if not config.schema_file.exists():
        raise FileNotFoundError(f"File schema non trovato: {config.schema_file}")
    
    with open(config.schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Esegui lo schema
    conn = get_db_connection()
    with get_db_cursor() as cursor:
        cursor.executescript(schema_sql)
    
    config.logger.info("Database inizializzato con successo")
    
    # Inserisci categorie predefinite se non esistono
    _inserisci_categorie_predefinite()


def _inserisci_categorie_predefinite():
    """Inserisce le categorie predefinite se non esistono."""
    from src.models.models import CATEGORIE_PREDEFINITE
    
    with get_db_cursor() as cursor:
        for nome_categoria, tipo_macro in CATEGORIE_PREDEFINITE:
            cursor.execute(
                """
                INSERT OR IGNORE INTO categoria_transazione (nome_categoria, tipo_macro)
                VALUES (?, ?)
                """,
                (nome_categoria, tipo_macro)
            )
    
    logging.info("Categorie predefinite inserite")


def backup_database(backup_dir: Optional[str] = None) -> str:
    """
    Crea un backup del database.
    
    Args:
        backup_dir: Directory per il backup. Se None, usa 'data/backups'
    
    Returns:
        Path del file di backup creato
    """
    config = DatabaseConfig()
    
    if backup_dir is None:
        backup_dir = Path(config.db_path).parent / "backups"
    else:
        backup_dir = Path(backup_dir)
    
    backup_dir.mkdir(exist_ok=True)
    
    # Nome file con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.db"
    
    # Copia il database
    import shutil
    shutil.copy2(config.db_path, backup_file)
    
    config.logger.info(f"Backup creato: {backup_file}")
    return str(backup_file)


def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Esegue una query SELECT e ritorna i risultati.
    
    Args:
        query: Query SQL da eseguire
        params: Parametri per la query (optional)
    
    Returns:
        Lista di dizionari con i risultati
    """
    with get_db_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Converti Row objects in dizionari
        return [dict(row) for row in cursor.fetchall()]


def execute_non_query(query: str, params: Optional[tuple] = None) -> int:
    """
    Esegue una query INSERT/UPDATE/DELETE.
    
    Args:
        query: Query SQL da eseguire
        params: Parametri per la query (optional)
    
    Returns:
        Numero di righe affected o lastrowid per INSERT
    """
    with get_db_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Per INSERT, ritorna l'ID inserito
        if query.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        else:
            return cursor.rowcount


def log_audit(tabella: str, operazione: str, id_record: int, 
              dati_precedenti: Optional[Dict] = None, 
              dati_nuovi: Optional[Dict] = None):
    """
    Registra un'operazione nell'audit log.
    
    Args:
        tabella: Nome della tabella
        operazione: Tipo di operazione (INSERT, UPDATE, DELETE)
        id_record: ID del record modificato
        dati_precedenti: Dati prima della modifica (per UPDATE/DELETE)
        dati_nuovi: Dati dopo la modifica (per INSERT/UPDATE)
    """
    query = """
        INSERT INTO audit_log (tabella, operazione, id_record, dati_precedenti, dati_nuovi)
        VALUES (?, ?, ?, ?, ?)
    """
    
    params = (
        tabella,
        operazione,
        id_record,
        json.dumps(dati_precedenti) if dati_precedenti else None,
        json.dumps(dati_nuovi) if dati_nuovi else None
    )
    
    execute_non_query(query, params)


def get_database_stats() -> Dict[str, Any]:
    """
    Ottiene statistiche sul database.
    
    Returns:
        Dizionario con statistiche del database
    """
    stats = {}
    
    # Conta record per tabella
    tables = ['proprieta', 'conto_finanziario', 'categoria_transazione', 'transazione']
    
    for table in tables:
        query = f"SELECT COUNT(*) as count FROM {table}"
        result = execute_query(query)
        stats[f"{table}_count"] = result[0]['count'] if result else 0
    
    # Dimensione database
    config = DatabaseConfig()
    if os.path.exists(config.db_path):
        stats['database_size_mb'] = os.path.getsize(config.db_path) / (1024 * 1024)
    
    # Ultima transazione
    query = "SELECT MAX(created_at) as last_transaction FROM transazione"
    result = execute_query(query)
    stats['last_transaction'] = result[0]['last_transaction'] if result and result[0]['last_transaction'] else None
    
    return stats


# Funzioni utility per verifiche comuni
def verifica_esistenza_id(tabella: str, nome_colonna_id: str, id_valore: int) -> bool:
    """
    Verifica se un ID esiste in una tabella.
    
    Args:
        tabella: Nome della tabella
        nome_colonna_id: Nome della colonna ID
        id_valore: Valore ID da verificare
    
    Returns:
        True se l'ID esiste, False altrimenti
    """
    query = f"SELECT 1 FROM {tabella} WHERE {nome_colonna_id} = ? LIMIT 1"
    result = execute_query(query, (id_valore,))
    return len(result) > 0


def verifica_unicita(tabella: str, nome_colonna: str, valore: str, 
                     escludi_id: Optional[int] = None, 
                     nome_colonna_id: Optional[str] = None) -> bool:
    """
    Verifica se un valore è unico in una colonna.
    
    Args:
        tabella: Nome della tabella
        nome_colonna: Nome della colonna da verificare
        valore: Valore da verificare
        escludi_id: ID da escludere dal controllo (per UPDATE)
        nome_colonna_id: Nome della colonna ID se si usa escludi_id
    
    Returns:
        True se il valore è unico, False altrimenti
    """
    if escludi_id and nome_colonna_id:
        query = f"SELECT 1 FROM {tabella} WHERE {nome_colonna} = ? AND {nome_colonna_id} != ? LIMIT 1"
        result = execute_query(query, (valore, escludi_id))
    else:
        query = f"SELECT 1 FROM {tabella} WHERE {nome_colonna} = ? LIMIT 1"
        result = execute_query(query, (valore,))
    
    return len(result) == 0