from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from enum import Enum

class TipoProprieta(Enum):
    """Enumerazione per i tipi di proprietà gestiti."""
    POSSESSO_USO_PERSONALE = "Possesso ad uso personale"
    POSSESSO_AFFITTATA = "Possesso affittata"
    AFFITTO_PASSIVO = "Affitto passivo"

@dataclass
class Proprieta:
    """
    Rappresenta una proprietà immobiliare nel sistema.
    Può essere una proprietà posseduta (ad uso personale o affittata)
    o una proprietà in affitto passivo (dove si vive pagando affitto).
    """
    id_proprieta: Optional[int] = None
    nome_o_indirizzo_breve: str = ""
    tipo: TipoProprieta = TipoProprieta.POSSESSO_USO_PERSONALE
    data_acquisizione_o_inizio_contratto_affitto: Optional[date] = None
    valore_acquisto_o_stima_attuale: Optional[float] = None
    canone_affitto_mensile_attivo: Optional[float] = None
    canone_affitto_mensile_passivo: Optional[float] = None
    eventuali_note_legali_o_scadenze_contrattuali: Optional[str] = None

    def __post_init__(self):
        self._valida()

    def _valida(self):
        if not self.nome_o_indirizzo_breve or not self.nome_o_indirizzo_breve.strip():
            raise ValueError("Il nome/indirizzo della proprietà è obbligatorio")
        if self.tipo in [TipoProprieta.POSSESSO_USO_PERSONALE, TipoProprieta.POSSESSO_AFFITTATA]:
            if self.valore_acquisto_o_stima_attuale is None:
                raise ValueError(f"Il valore di acquisto/stima è obbligatorio per proprietà di tipo {self.tipo.value}")
            if self.valore_acquisto_o_stima_attuale <= 0:
                raise ValueError("Il valore di acquisto/stima deve essere positivo")
        if self.tipo == TipoProprieta.POSSESSO_AFFITTATA:
            if self.canone_affitto_mensile_attivo is None:
                raise ValueError("Il canone di affitto attivo è obbligatorio per proprietà affittate")
            if self.canone_affitto_mensile_attivo <= 0:
                raise ValueError("Il canone di affitto attivo deve essere positivo")
        if self.tipo == TipoProprieta.AFFITTO_PASSIVO:
            if self.canone_affitto_mensile_passivo is None:
                raise ValueError("Il canone di affitto passivo è obbligatorio per affitti passivi")
            if self.canone_affitto_mensile_passivo <= 0:
                raise ValueError("Il canone di affitto passivo deve essere positivo")

    def calcola_rendimento_annuo_lordo(self) -> Optional[float]:
        if (self.tipo == TipoProprieta.POSSESSO_AFFITTATA and 
            self.canone_affitto_mensile_attivo and 
            self.valore_acquisto_o_stima_attuale):
            rendita_annua = self.canone_affitto_mensile_attivo * 12
            return (rendita_annua / self.valore_acquisto_o_stima_attuale) * 100
        return None

    def __str__(self) -> str:
        return f"Proprietà: {self.nome_o_indirizzo_breve} ({self.tipo.value})"
