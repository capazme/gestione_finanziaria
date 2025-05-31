"""
# conto_repository.py
Repository per la gestione dei conti finanziari.
"""

from typing import List, Optional, Dict
from src.models.models import ContoFinanziario, TipoConto
from src.repositories.base_repository import BaseRepository
from src.database.database_connection import verifica_unicita, execute_query


class ContoRepository(BaseRepository[ContoFinanziario]):
    """Repository per la gestione dei conti finanziari."""

    @property
    def table_name(self) -> str:
        return "conto_finanziario"

    @property
    def id_column(self) -> str:
        return "id_conto"

    @property
    def entity_class(self):
        return ContoFinanziario

    def to_entity(self, row: Dict) -> ContoFinanziario:
        return ContoFinanziario(
            id_conto=row["id_conto"],
            nome_conto=row["nome_conto"],
            saldo_iniziale=row["saldo_iniziale"],
            tipo_conto=TipoConto(row["tipo_conto"]),
            saldo_attuale=row["saldo_attuale"]
        )

    def to_dict(self, entity: ContoFinanziario) -> Dict:
        return {
            "id_conto": entity.id_conto,
            "nome_conto": entity.nome_conto,
            "saldo_iniziale": entity.saldo_iniziale,
            "tipo_conto": entity.tipo_conto.value if hasattr(entity.tipo_conto, "value") else str(entity.tipo_conto),
            "saldo_attuale": entity.saldo_attuale
        }

    def create(self, entity: ContoFinanziario) -> ContoFinanziario:
        # Verifica unicità nome_conto
        if not verifica_unicita(self.table_name, "nome_conto", entity.nome_conto):
            raise ValueError(f"Conto '{entity.nome_conto}' già esistente")
        return super().create(entity)

    def update(self, entity: ContoFinanziario) -> ContoFinanziario:
        # Verifica unicità nome_conto escludendo l'ID corrente
        if not verifica_unicita(self.table_name, "nome_conto", entity.nome_conto, entity.id_conto, self.id_column):
            raise ValueError(f"Conto '{entity.nome_conto}' già esistente")
        return super().update(entity)

    def get_by_nome(self, nome_conto: str) -> Optional[ContoFinanziario]:
        query = f"SELECT * FROM {self.table_name} WHERE nome_conto = ?"
        results = execute_query(query, (nome_conto,))
        if results:
            return self.to_entity(results[0])
        return None

    def get_by_tipo(self, tipo_conto: str) -> List[ContoFinanziario]:
        query = f"SELECT * FROM {self.table_name} WHERE tipo_conto = ? ORDER BY nome_conto"
        results = execute_query(query, (tipo_conto,))
        return [self.to_entity(row) for row in results]
