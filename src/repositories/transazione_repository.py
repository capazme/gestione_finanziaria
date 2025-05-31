"""
# transazione_repository.py
Repository per la gestione delle transazioni finanziarie.
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from src.models.models import Transazione, TipoFlusso
from src.repositories.base_repository import BaseRepository
from src.database.database_connection import (
    verifica_esistenza_id, execute_query
)

class TransazioneRepository(BaseRepository[Transazione]):
    """Repository per la gestione delle transazioni finanziarie."""

    @property
    def table_name(self) -> str:
        return "transazione"

    @property
    def id_column(self) -> str:
        return "id_transazione"

    @property
    def entity_class(self):
        return Transazione

    def to_entity(self, row: Dict) -> Transazione:
        # Conversione data, bool, enum
        data_trans = datetime.strptime(row["data"], "%Y-%m-%d").date()
        flag_fiscale = bool(row["flag_deducibile_o_rilevante_fiscalmente"])
        tipo_flusso = TipoFlusso(row["tipo_flusso"])
        return Transazione(
            id_transazione=row["id_transazione"],
            data=data_trans,
            importo=row["importo"],
            descrizione=row["descrizione"],
            id_categoria=row["id_categoria"],
            id_conto_finanziario=row["id_conto_finanziario"],
            id_proprieta_associata=row["id_proprieta_associata"],
            tipo_flusso=tipo_flusso,
            flag_deducibile_o_rilevante_fiscalmente=flag_fiscale,
            note_aggiuntive=row["note_aggiuntive"]
        )

    def to_dict(self, entity: Transazione) -> Dict:
        data_str = entity.data.strftime("%Y-%m-%d") if isinstance(entity.data, date) else entity.data
        return {
            "id_transazione": entity.id_transazione,
            "data": data_str,
            "importo": entity.importo,
            "descrizione": entity.descrizione,
            "id_categoria": entity.id_categoria,
            "id_conto_finanziario": entity.id_conto_finanziario,
            "id_proprieta_associata": entity.id_proprieta_associata,
            "tipo_flusso": entity.tipo_flusso.value if hasattr(entity.tipo_flusso, "value") else str(entity.tipo_flusso),
            "flag_deducibile_o_rilevante_fiscalmente": int(entity.flag_deducibile_o_rilevante_fiscalmente),
            "note_aggiuntive": entity.note_aggiuntive
        }

    def _valida_fk(self, entity: Transazione):
        # Verifica esistenza FK obbligatorie
        if not verifica_esistenza_id("categoria_transazione", "id_categoria", entity.id_categoria):
            raise ValueError(f"Categoria con ID {entity.id_categoria} non esistente")
        if not verifica_esistenza_id("conto_finanziario", "id_conto", entity.id_conto_finanziario):
            raise ValueError(f"Conto finanziario con ID {entity.id_conto_finanziario} non esistente")
        if entity.id_proprieta_associata:
            if not verifica_esistenza_id("proprieta", "id_proprieta", entity.id_proprieta_associata):
                raise ValueError(f"Proprietà con ID {entity.id_proprieta_associata} non esistente")

    def create(self, entity: Transazione) -> Transazione:
        self._valida_fk(entity)
        return super().create(entity)

    def update(self, entity: Transazione) -> Transazione:
        self._valida_fk(entity)
        return super().update(entity)

    def get_by_periodo(self, data_inizio: date, data_fine: date, order_by: Optional[str] = "data DESC") -> List[Transazione]:
        query = f"SELECT * FROM {self.table_name} WHERE data >= ? AND data <= ?"
        if order_by:
            query += f" ORDER BY {order_by}"
        results = execute_query(query, (data_inizio.strftime("%Y-%m-%d"), data_fine.strftime("%Y-%m-%d")))
        return [self.to_entity(row) for row in results]

    def get_by_conto_id(self, id_conto: int, data_inizio: Optional[date] = None, data_fine: Optional[date] = None) -> List[Transazione]:
        query = f"SELECT * FROM {self.table_name} WHERE id_conto_finanziario = ?"
        params = [id_conto]
        if data_inizio:
            query += " AND data >= ?"
            params.append(data_inizio.strftime("%Y-%m-%d"))
        if data_fine:
            query += " AND data <= ?"
            params.append(data_fine.strftime("%Y-%m-%d"))
        query += " ORDER BY data DESC"
        results = execute_query(query, tuple(params))
        return [self.to_entity(row) for row in results]

    def get_by_categoria_id(self, id_categoria: int, data_inizio: Optional[date] = None, data_fine: Optional[date] = None) -> List[Transazione]:
        query = f"SELECT * FROM {self.table_name} WHERE id_categoria = ?"
        params = [id_categoria]
        if data_inizio:
            query += " AND data >= ?"
            params.append(data_inizio.strftime("%Y-%m-%d"))
        if data_fine:
            query += " AND data <= ?"
            params.append(data_fine.strftime("%Y-%m-%d"))
        query += " ORDER BY data DESC"
        results = execute_query(query, tuple(params))
        return [self.to_entity(row) for row in results]

    def get_by_proprieta_id(self, id_proprieta: int, data_inizio: Optional[date] = None, data_fine: Optional[date] = None) -> List[Transazione]:
        query = f"SELECT * FROM {self.table_name} WHERE id_proprieta_associata = ?"
        params = [id_proprieta]
        if data_inizio:
            query += " AND data >= ?"
            params.append(data_inizio.strftime("%Y-%m-%d"))
        if data_fine:
            query += " AND data <= ?"
            params.append(data_fine.strftime("%Y-%m-%d"))
        query += " ORDER BY data DESC"
        results = execute_query(query, tuple(params))
        return [self.to_entity(row) for row in results]

    def get_by_tipo_flusso(self, tipo_flusso: TipoFlusso, data_inizio: Optional[date] = None, data_fine: Optional[date] = None) -> List[Transazione]:
        query = f"SELECT * FROM {self.table_name} WHERE tipo_flusso = ?"
        params = [tipo_flusso.value]
        if data_inizio:
            query += " AND data >= ?"
            params.append(data_inizio.strftime("%Y-%m-%d"))
        if data_fine:
            query += " AND data <= ?"
            params.append(data_fine.strftime("%Y-%m-%d"))
        query += " ORDER BY data DESC"
        results = execute_query(query, tuple(params))
        return [self.to_entity(row) for row in results]

    def get_fiscalmente_rilevanti(self, data_inizio: date, data_fine: date) -> List[Transazione]:
        query = f"SELECT * FROM {self.table_name} WHERE flag_deducibile_o_rilevante_fiscalmente = 1 AND data >= ? AND data <= ? ORDER BY data DESC"
        results = execute_query(query, (data_inizio.strftime("%Y-%m-%d"), data_fine.strftime("%Y-%m-%d")))
        return [self.to_entity(row) for row in results]

    def get_entrate_da_affitto_per_proprieta(self, id_proprieta: int, data_inizio: date, data_fine: date) -> List[Transazione]:
        # Recupera solo le entrate (importo > 0) associate a una proprietà, e a categorie "Affitto Incassato ..."
        query = f"""
            SELECT t.* FROM {self.table_name} t
            JOIN categoria_transazione c ON t.id_categoria = c.id_categoria
            WHERE t.id_proprieta_associata = ?
              AND t.importo > 0
              AND c.nome_categoria LIKE 'Affitto Incassato%'
              AND t.data >= ? AND t.data <= ?
            ORDER BY t.data DESC
        """
        results = execute_query(query, (id_proprieta, data_inizio.strftime("%Y-%m-%d"), data_fine.strftime("%Y-%m-%d")))
        return [self.to_entity(row) for row in results]
