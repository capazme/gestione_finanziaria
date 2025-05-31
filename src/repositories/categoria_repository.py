"""
# categoria_repository.py
Repository per la gestione delle categorie di transazione.
"""

from typing import List, Optional, Dict
from src.models.models import CategoriaTransazione
from src.repositories.base_repository import BaseRepository
from src.database.database_connection import verifica_unicita


class CategoriaRepository(BaseRepository[CategoriaTransazione]):
    """Repository per la gestione delle categorie di transazione."""
    
    @property
    def table_name(self) -> str:
        return "categoria_transazione"
    
    @property
    def id_column(self) -> str:
        return "id_categoria"
    
    @property
    def entity_class(self):
        return CategoriaTransazione
    
    def to_entity(self, row: Dict) -> CategoriaTransazione:
        """Converte una riga del database in CategoriaTransazione."""
        return CategoriaTransazione(
            id_categoria=row['id_categoria'],
            nome_categoria=row['nome_categoria'],
            tipo_macro=row['tipo_macro']
        )
    
    def to_dict(self, entity: CategoriaTransazione) -> Dict:
        """Converte CategoriaTransazione in dizionario per il database."""
        return {
            'id_categoria': entity.id_categoria,
            'nome_categoria': entity.nome_categoria,
            'tipo_macro': entity.tipo_macro
        }
    
    def create(self, entity: CategoriaTransazione) -> CategoriaTransazione:
        """
        Crea una nuova categoria con validazione unicità nome.
        
        Args:
            entity: Categoria da creare
            
        Returns:
            Categoria creata con ID
            
        Raises:
            ValueError: Se il nome categoria esiste già
        """
        # Verifica unicità nome
        if not verifica_unicita(self.table_name, 'nome_categoria', entity.nome_categoria):
            raise ValueError(f"Categoria '{entity.nome_categoria}' già esistente")
        
        return super().create(entity)
    
    def update(self, entity: CategoriaTransazione) -> CategoriaTransazione:
        """
        Aggiorna una categoria con validazione unicità nome.
        
        Args:
            entity: Categoria da aggiornare
            
        Returns:
            Categoria aggiornata
            
        Raises:
            ValueError: Se il nuovo nome esiste già
        """
        # Verifica unicità nome escludendo l'ID corrente
        if not verifica_unicita(self.table_name, 'nome_categoria', 
                               entity.nome_categoria, entity.id_categoria, 
                               self.id_column):
            raise ValueError(f"Categoria '{entity.nome_categoria}' già esistente")
        
        return super().update(entity)
    
    def get_by_nome(self, nome_categoria: str) -> Optional[CategoriaTransazione]:
        """
        Recupera una categoria per nome.
        
        Args:
            nome_categoria: Nome della categoria
            
        Returns:
            Categoria se trovata, None altrimenti
        """
        query = f"SELECT * FROM {self.table_name} WHERE nome_categoria = ?"
        results = execute_query(query, (nome_categoria,))
        
        if results:
            return self.to_entity(results[0])
        return None
    
    def get_by_tipo_macro(self, tipo_macro: str) -> List[CategoriaTransazione]:
        """
        Recupera tutte le categorie di un tipo macro.
        
        Args:
            tipo_macro: Tipo macro da filtrare
            
        Returns:
            Lista di categorie del tipo specificato
        """
        query = f"SELECT * FROM {self.table_name} WHERE tipo_macro = ? ORDER BY nome_categoria"
        results = execute_query(query, (tipo_macro,))
        return [self.to_entity(row) for row in results]
    
    def get_categorie_immobiliari(self) -> List[CategoriaTransazione]:
        """
        Recupera tutte le categorie immobiliari.
        
        Returns:
            Lista di categorie immobiliari
        """
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE tipo_macro LIKE 'Immobile %' 
            ORDER BY tipo_macro, nome_categoria
        """
        results = execute_query(query)
        return [self.to_entity(row) for row in results]
    
    def get_categorie_per_proprieta(self, nome_proprieta: str) -> List[CategoriaTransazione]:
        """
        Recupera tutte le categorie associate a una specifica proprietà.
        
        Args:
            nome_proprieta: Nome della proprietà
            
        Returns:
            Lista di categorie per la proprietà
        """
        tipo_macro = f"Immobile {nome_proprieta}"
        return self.get_by_tipo_macro(tipo_macro)
    
    def verifica_categoria_in_uso(self, id_categoria: int) -> bool:
        """
        Verifica se una categoria è utilizzata in transazioni.
        
        Args:
            id_categoria: ID della categoria
            
        Returns:
            True se in uso, False altrimenti
        """
        query = "SELECT 1 FROM transazione WHERE id_categoria = ? LIMIT 1"
        results = execute_query(query, (id_categoria,))
        return len(results) > 0
    
    def delete(self, entity_id: int) -> bool:
        """
        Elimina una categoria solo se non utilizzata.
        
        Args:
            entity_id: ID della categoria
            
        Returns:
            True se eliminata, False altrimenti
            
        Raises:
            ValueError: Se la categoria è in uso
        """
        if self.verifica_categoria_in_uso(entity_id):
            raise ValueError("Impossibile eliminare categoria in uso nelle transazioni")
        
        return super().delete(entity_id)
    
    def get_statistiche_utilizzo(self) -> List[Dict]:
        """
        Ottiene statistiche sull'utilizzo delle categorie.
        
        Returns:
            Lista con statistiche per categoria
        """
        query = """
            SELECT 
                c.id_categoria,
                c.nome_categoria,
                c.tipo_macro,
                COUNT(t.id_transazione) as numero_transazioni,
                SUM(CASE WHEN t.importo > 0 THEN t.importo ELSE 0 END) as totale_entrate,
                SUM(CASE WHEN t.importo < 0 THEN ABS(t.importo) ELSE 0 END) as totale_uscite
            FROM categoria_transazione c
            LEFT JOIN transazione t ON c.id_categoria = t.id_categoria
            GROUP BY c.id_categoria
            ORDER BY numero_transazioni DESC
        """
        results = execute_query(query)
        return [dict(row) for row in results]
    
    def crea_categorie_per_nuova_proprieta(self, nome_proprieta: str, 
                                          tipo_proprieta: str) -> List[CategoriaTransazione]:
        """
        Crea le categorie standard per una nuova proprietà.
        
        Args:
            nome_proprieta: Nome della proprietà
            tipo_proprieta: Tipo di proprietà (enum value)
            
        Returns:
            Lista delle categorie create
        """
        from src.models.models import crea_categorie_per_proprieta, TipoProprieta
        
        # Converti stringa in enum
        tipo_enum = TipoProprieta(tipo_proprieta)
        
        # Ottieni lista categorie da creare
        categorie_da_creare = crea_categorie_per_proprieta(nome_proprieta, tipo_enum)
        
        categorie_create = []
        for nome_cat, tipo_macro in categorie_da_creare:
            try:
                categoria = CategoriaTransazione(
                    nome_categoria=nome_cat,
                    tipo_macro=tipo_macro
                )
                categoria_creata = self.create(categoria)
                categorie_create.append(categoria_creata)
                self.logger.info(f"Creata categoria: {nome_cat}")
            except ValueError as e:
                # Categoria già esistente, skip
                self.logger.warning(f"Categoria già esistente: {nome_cat}")
        
        return categorie_create