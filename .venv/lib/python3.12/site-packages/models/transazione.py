from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Dict
from enum import Enum
from .categoria_transazione import CategoriaTransazione
from .conto_finanziario import ContoFinanziario
from .proprieta import Proprieta

class TipoFlusso(Enum):
    """Enumerazione per i tipi di flusso delle transazioni."""
    PERSONALE = "Personale"
    IMMOBILIARE = "Immobiliare"
    FISCALE = "Fiscale"

@dataclass
class Transazione:
    """
    Rappresenta una transazione finanziaria nel sistema.
    Le transazioni sono collegate a conti, categorie e opzionalmente a proprietà.
    Gli importi positivi rappresentano entrate, quelli negativi uscite.
    """
    id_transazione: Optional[int] = None
    data: date = field(default_factory=date.today)
    importo: float = 0.0
    descrizione: str = ""
    id_categoria: int = 0
    id_conto_finanziario: int = 0
    id_proprieta_associata: Optional[int] = None
    tipo_flusso: TipoFlusso = TipoFlusso.PERSONALE
    flag_deducibile_o_rilevante_fiscalmente: bool = False
    note_aggiuntive: Optional[str] = None
    categoria: Optional[CategoriaTransazione] = field(default=None, init=False)
    conto: Optional[ContoFinanziario] = field(default=None, init=False)
    proprieta: Optional[Proprieta] = field(default=None, init=False)

    def __post_init__(self):
        self._valida()

    def _valida(self):
        if not self.descrizione or not self.descrizione.strip():
            raise ValueError("La descrizione della transazione è obbligatoria")
        if not isinstance(self.importo, (int, float)):
            raise ValueError("L'importo deve essere un numero")
        if self.importo == 0:
            raise ValueError("L'importo non può essere zero")
        if self.id_categoria <= 0:
            raise ValueError("ID categoria non valido")
        if self.id_conto_finanziario <= 0:
            raise ValueError("ID conto finanziario non valido")
        if self.data > date.today():
            raise ValueError("La data della transazione non può essere nel futuro")

    def è_entrata(self) -> bool:
        return self.importo > 0

    def è_uscita(self) -> bool:
        return self.importo < 0

    def get_importo_assoluto(self) -> float:
        return abs(self.importo)

    def get_mese_anno(self) -> str:
        return self.data.strftime("%m/%Y")

    def get_anno(self) -> int:
        return self.data.year

    def to_dict_for_export(self) -> Dict:
        return {
            "Data": self.data.strftime("%d/%m/%Y"),
            "Importo": f"{self.importo:.2f}",
            "Descrizione": self.descrizione,
            "Categoria": self.categoria.nome_categoria if self.categoria else f"ID: {self.id_categoria}",
            "Conto": self.conto.nome_conto if self.conto else f"ID: {self.id_conto_finanziario}",
            "Proprietà": self.proprieta.nome_o_indirizzo_breve if self.proprieta else "N/A",
            "Tipo Flusso": self.tipo_flusso.value,
            "Deducibile": "Sì" if self.flag_deducibile_o_rilevante_fiscalmente else "No",
            "Note": self.note_aggiuntive or ""
        }

    def __str__(self) -> str:
        tipo = "+" if self.è_entrata() else "-"
        return f"{self.data} {tipo}€{abs(self.importo):.2f} - {self.descrizione}"
