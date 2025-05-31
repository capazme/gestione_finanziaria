"""
# base_repository.py
Repository base con operazioni CRUD comuni per tutte le entità.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from dataclasses import dataclass, fields, asdict
import logging
from datetime import date

from src.database.database_connection import (
    get_db_cursor, execute_query, execute_non_query, 
    log_audit, verifica_esistenza_id, verifica_unicita
)


T = TypeVar('T')  # Tipo generico per le entità


class BaseRepository(Generic[T], ABC):
    """
    Repository base astratto che implementa operazioni CRUD comuni.
    
    Le classi derivate devono implementare i metodi astratti
    per specificare tabella, mapping e conversioni.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Nome della tabella nel database."""
        pass
    
    @property
    @abstractmethod
    def id_column(self) -> str:
        """Nome della colonna ID primaria."""
        pass
    
    @property
    @abstractmethod
    def entity_class(self) -> Type[T]:
        """Classe dell'entità gestita dal repository."""
        pass
    
    @abstractmethod
    def to_entity(self, row: Dict[str, Any]) -> T:
        """
        Converte una riga del database in entità.
        
        Args:
            row: Dizionario con i dati della riga
            
        Returns:
            Istanza dell'entità
        """
        pass
    
    @abstractmethod
    def to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Converte un'entità in dizionario per il database.
        
        Args:
            entity: Istanza dell'entità
            
        Returns:
            Dizionario con i dati per il database
        """
        pass
    
    def create(self, entity: T) -> T:
        """
        Crea una nuova entità nel database.
        
        Args:
            entity: Entità da creare
            
        Returns:
            Entità creata con ID assegnato
            
        Raises:
            ValueError: Se la validazione fallisce
        """
        # Converti in dizionario e rimuovi l'ID (sarà autogenerato)
        data = self.to_dict(entity)
        data.pop(self.id_column, None)
        
        # Costruisci query INSERT
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        
        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        # Esegui insert
        new_id = execute_non_query(query, tuple(data.values()))
        
        # Log audit
        log_audit(self.table_name, "INSERT", new_id, dati_nuovi=data)
        
        # Ricarica l'entità per avere tutti i campi aggiornati
        return self.get_by_id(new_id)
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Recupera un'entità per ID.
        
        Args:
            entity_id: ID dell'entità
            
        Returns:
            Entità se trovata, None altrimenti
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self.id_column} = ?"
        results = execute_query(query, (entity_id,))
        
        if results:
            return self.to_entity(results[0])
        return None
    
    def get_all(self, order_by: Optional[str] = None) -> List[T]:
        """
        Recupera tutte le entità.
        
        Args:
            order_by: Campo per ordinamento (optional)
            
        Returns:
            Lista di tutte le entità
        """
        query = f"SELECT * FROM {self.table_name}"
        if order_by:
            query += f" ORDER BY {order_by}"
        
        results = execute_query(query)
        return [self.to_entity(row) for row in results]
    
    def update(self, entity: T) -> T:
        """
        Aggiorna un'entità esistente.
        
        Args:
            entity: Entità da aggiornare
            
        Returns:
            Entità aggiornata
            
        Raises:
            ValueError: Se l'entità non esiste
        """
        data = self.to_dict(entity)
        entity_id = data.pop(self.id_column)
        
        # Verifica che l'entità esista
        if not verifica_esistenza_id(self.table_name, self.id_column, entity_id):
            raise ValueError(f"{self.entity_class.__name__} con ID {entity_id} non trovato")
        
        # Recupera dati precedenti per audit
        old_data = execute_query(
            f"SELECT * FROM {self.table_name} WHERE {self.id_column} = ?", 
            (entity_id,)
        )[0]
        
        # Costruisci query UPDATE
        set_clauses = [f"{col} = ?" for col in data.keys()]
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE {self.id_column} = ?
        """
        
        # Esegui update
        params = list(data.values()) + [entity_id]
        execute_non_query(query, tuple(params))
        
        # Log audit
        log_audit(self.table_name, "UPDATE", entity_id, 
                 dati_precedenti=dict(old_data), dati_nuovi=data)
        
        # Ricarica l'entità
        return self.get_by_id(entity_id)
    
    def delete(self, entity_id: int) -> bool:
        """
        Elimina un'entità.
        
        Args:
            entity_id: ID dell'entità da eliminare
            
        Returns:
            True se eliminata, False se non trovata
        """
        # Recupera dati per audit
        old_entity = self.get_by_id(entity_id)
        if not old_entity:
            return False
        
        old_data = self.to_dict(old_entity)
        
        # Esegui delete
        query = f"DELETE FROM {self.table_name} WHERE {self.id_column} = ?"
        rows_affected = execute_non_query(query, (entity_id,))
        
        if rows_affected > 0:
            # Log audit
            log_audit(self.table_name, "DELETE", entity_id, 
                     dati_precedenti=old_data)
            return True
        
        return False
    
    def exists(self, entity_id: int) -> bool:
        """
        Verifica se un'entità esiste.
        
        Args:
            entity_id: ID dell'entità
            
        Returns:
            True se esiste, False altrimenti
        """
        return verifica_esistenza_id(self.table_name, self.id_column, entity_id)
    
    def count(self, where_clause: Optional[str] = None, 
              params: Optional[tuple] = None) -> int:
        """
        Conta le entità che soddisfano una condizione.
        
        Args:
            where_clause: Clausola WHERE SQL (optional)
            params: Parametri per la clausola WHERE
            
        Returns:
            Numero di entità
        """
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = execute_query(query, params)
        return result[0]['count'] if result else 0