"""
# proprieta_repository.py
Repository per la gestione delle proprietà immobiliari.
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from src.models.models import Proprieta, TipoProprieta
from src.repositories.base_repository import BaseRepository
from src.database.database_connection import verifica_unicita, execute_query

class ProprietaRepository(BaseRepository[Proprieta]):
    """Repository per la gestione delle proprietà immobiliari."""

    @property
    def table_name(self) -> str:
        return "proprieta"

    @property
    def id_column(self) -> str:
        return "id_proprieta"

    @property
    def entity_class(self):
        return Proprieta

    def to_entity(self, row: Dict) -> Proprieta:
        # Gestione conversione date e float
        data_acquisizione = None
        if row["data_acquisizione_o_inizio_contratto_affitto"]:
            data_acquisizione = datetime.strptime(row["data_acquisizione_o_inizio_contratto_affitto"], "%Y-%m-%d").date()
        return Proprieta(
            id_proprieta=row["id_proprieta"],
            nome_o_indirizzo_breve=row["nome_o_indirizzo_breve"],
            tipo=TipoProprieta(row["tipo"]),
            data_acquisizione_o_inizio_contratto_affitto=data_acquisizione,
            valore_acquisto_o_stima_attuale=row["valore_acquisto_o_stima_attuale"],
            canone_affitto_mensile_attivo=row["canone_affitto_mensile_attivo"],
            canone_affitto_mensile_passivo=row["canone_affitto_mensile_passivo"],
            eventuali_note_legali_o_scadenze_contrattuali=row["eventuali_note_legali_o_scadenze_contrattuali"]
        )

    def to_dict(self, entity: Proprieta) -> Dict:
        # Gestione conversione date e float
        data_acquisizione = (
            entity.data_acquisizione_o_inizio_contratto_affitto.strftime("%Y-%m-%d")
            if entity.data_acquisizione_o_inizio_contratto_affitto else None
        )
        return {
            "id_proprieta": entity.id_proprieta,
            "nome_o_indirizzo_breve": entity.nome_o_indirizzo_breve,
            "tipo": entity.tipo.value if hasattr(entity.tipo, "value") else str(entity.tipo),
            "data_acquisizione_o_inizio_contratto_affitto": data_acquisizione,
            "valore_acquisto_o_stima_attuale": entity.valore_acquisto_o_stima_attuale,
            "canone_affitto_mensile_attivo": entity.canone_affitto_mensile_attivo,
            "canone_affitto_mensile_passivo": entity.canone_affitto_mensile_passivo,
            "eventuali_note_legali_o_scadenze_contrattuali": entity.eventuali_note_legali_o_scadenze_contrattuali
        }

    def create(self, entity: Proprieta) -> Proprieta:
        # Verifica unicità nome_o_indirizzo_breve
        if not verifica_unicita(self.table_name, "nome_o_indirizzo_breve", entity.nome_o_indirizzo_breve):
            raise ValueError(f"Proprietà '{entity.nome_o_indirizzo_breve}' già esistente")
        return super().create(entity)

    def update(self, entity: Proprieta) -> Proprieta:
        # Verifica unicità nome_o_indirizzo_breve escludendo l'ID corrente
        if not verifica_unicita(self.table_name, "nome_o_indirizzo_breve", entity.nome_o_indirizzo_breve, entity.id_proprieta, self.id_column):
            raise ValueError(f"Proprietà '{entity.nome_o_indirizzo_breve}' già esistente")
        return super().update(entity)

    def get_by_nome_o_indirizzo(self, nome: str) -> Optional[Proprieta]:
        query = f"SELECT * FROM {self.table_name} WHERE nome_o_indirizzo_breve = ?"
        results = execute_query(query, (nome,))
        if results:
            return self.to_entity(results[0])
        return None

    def get_by_tipo(self, tipo: TipoProprieta) -> List[Proprieta]:
        query = f"SELECT * FROM {self.table_name} WHERE tipo = ? ORDER BY nome_o_indirizzo_breve"
        results = execute_query(query, (tipo.value,))
        return [self.to_entity(row) for row in results]

    def delete(self, entity_id: int) -> bool:
        # Verifica se esistono transazioni associate
        query_trans = "SELECT 1 FROM transazione WHERE id_proprieta_associata = ? LIMIT 1"
        results_trans = execute_query(query_trans, (entity_id,))
        if results_trans:
            raise ValueError("Impossibile eliminare la proprietà: esistono transazioni associate.")

        # Verifica se esistono categorie associate (tipo_macro = 'Immobile [Nome Proprietà]')
        # Recupera il nome della proprietà
        prop = self.get_by_id(entity_id)
        if not prop:
            return False
        tipo_macro = f"Immobile {prop.nome_o_indirizzo_breve}"
        query_cat = "SELECT 1 FROM categoria_transazione WHERE tipo_macro = ? LIMIT 1"
        results_cat = execute_query(query_cat, (tipo_macro,))
        if results_cat:
            raise ValueError("Impossibile eliminare la proprietà: esistono categorie associate (tipo_macro).")

        return super().delete(entity_id)
