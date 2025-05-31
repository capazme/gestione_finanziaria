from dataclasses import dataclass
from typing import Optional
from enum import Enum

class TipoConto(Enum):
    """Enumerazione per i tipi di conto finanziario."""
    BANCARIO = "Bancario"
    RISPARMIO = "Risparmio"
    INVESTIMENTO_SEMPLICE = "Investimento Semplice"
    CONTANTI = "Contanti"

@dataclass
class ContoFinanziario:
    """
    Rappresenta un conto finanziario nel sistema.
    Può essere un conto bancario, di risparmio, investimento o contanti.
    Il saldo attuale viene calcolato dinamicamente dalle transazioni.
    """
    id_conto: Optional[int] = None
    nome_conto: str = ""
    saldo_iniziale: float = 0.0
    tipo_conto: TipoConto = TipoConto.BANCARIO
    saldo_attuale: Optional[float] = None  # Calcolato dinamicamente

    def __post_init__(self):
        self._valida()
        if self.saldo_attuale is None:
            self.saldo_attuale = self.saldo_iniziale

    def _valida(self):
        if not self.nome_conto or not self.nome_conto.strip():
            raise ValueError("Il nome del conto è obbligatorio")
        if not isinstance(self.saldo_iniziale, (int, float)):
            raise ValueError("Il saldo iniziale deve essere un numero")

    def aggiorna_saldo(self, nuovo_saldo: float):
        self.saldo_attuale = round(nuovo_saldo, 2)

    def __str__(self) -> str:
        return f"{self.nome_conto} ({self.tipo_conto.value}): €{self.saldo_attuale:.2f}"
