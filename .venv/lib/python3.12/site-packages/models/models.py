"""
Modelli dati per il sistema di gestione finanziaria e immobiliare.

Questo modulo contiene le dataclasses che rappresentano le entità principali
del sistema. Ogni classe include validazione dei dati e metodi utility.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict
from enum import Enum
import re

from .proprieta import Proprieta, TipoProprieta
from .conto_finanziario import ContoFinanziario, TipoConto
from .categoria_transazione import CategoriaTransazione, TipoMacroCategoria, CATEGORIE_PREDEFINITE, crea_categorie_per_proprieta
from .transazione import Transazione, TipoFlusso


class TipoProprieta(Enum):
    """Enumerazione per i tipi di proprietà gestiti."""
    POSSESSO_USO_PERSONALE = "Possesso ad uso personale"
    POSSESSO_AFFITTATA = "Possesso affittata"
    AFFITTO_PASSIVO = "Affitto passivo"


class TipoConto(Enum):
    """Enumerazione per i tipi di conto finanziario."""
    BANCARIO = "Bancario"
    RISPARMIO = "Risparmio"
    INVESTIMENTO_SEMPLICE = "Investimento Semplice"
    CONTANTI = "Contanti"


class TipoMacroCategoria(Enum):
    """Enumerazione per i tipi macro di categoria transazione."""
    PERSONALE = "Personale"
    IMMOBILE = "Immobile"  # Seguito da nome proprietà, es: "Immobile Casa Via Rossi"
    FISCALE_GENERALE = "Fiscale Generale"


class TipoFlusso(Enum):
    """Enumerazione per i tipi di flusso delle transazioni."""
    PERSONALE = "Personale"
    IMMOBILIARE = "Immobiliare"
    FISCALE = "Fiscale"


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
        """Validazione dei dati dopo l'inizializzazione."""
        self._valida()
    
    def _valida(self):
        """Esegue validazioni sui dati della proprietà."""
        if not self.nome_o_indirizzo_breve or not self.nome_o_indirizzo_breve.strip():
            raise ValueError("Il nome/indirizzo della proprietà è obbligatorio")
        
        # Validazioni specifiche per tipo
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
        """
        Calcola il rendimento annuo lordo per proprietà affittate.
        
        Returns:
            float: Percentuale di rendimento annuo lordo, o None se non applicabile
        """
        if (self.tipo == TipoProprieta.POSSESSO_AFFITTATA and 
            self.canone_affitto_mensile_attivo and 
            self.valore_acquisto_o_stima_attuale):
            rendita_annua = self.canone_affitto_mensile_attivo * 12
            return (rendita_annua / self.valore_acquisto_o_stima_attuale) * 100
        return None
    
    def __str__(self) -> str:
        return f"Proprietà: {self.nome_o_indirizzo_breve} ({self.tipo.value})"


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
        """Validazione dei dati dopo l'inizializzazione."""
        self._valida()
        if self.saldo_attuale is None:
            self.saldo_attuale = self.saldo_iniziale
    
    def _valida(self):
        """Esegue validazioni sui dati del conto."""
        if not self.nome_conto or not self.nome_conto.strip():
            raise ValueError("Il nome del conto è obbligatorio")
        
        if not isinstance(self.saldo_iniziale, (int, float)):
            raise ValueError("Il saldo iniziale deve essere un numero")
    
    def aggiorna_saldo(self, nuovo_saldo: float):
        """
        Aggiorna il saldo attuale del conto.
        
        Args:
            nuovo_saldo: Il nuovo saldo calcolato
        """
        self.saldo_attuale = round(nuovo_saldo, 2)
    
    def __str__(self) -> str:
        return f"{self.nome_conto} ({self.tipo_conto.value}): €{self.saldo_attuale:.2f}"


@dataclass
class CategoriaTransazione:
    """
    Rappresenta una categoria di transazione nel sistema.
    
    Le categorie sono organizzate in macro-categorie (Personale, Immobile, Fiscale).
    """
    id_categoria: Optional[int] = None
    nome_categoria: str = ""
    tipo_macro: str = ""  # Può includere nome proprietà, es: "Immobile Casa Via Rossi"
    
    def __post_init__(self):
        """Validazione dei dati dopo l'inizializzazione."""
        self._valida()
    
    def _valida(self):
        """Esegue validazioni sui dati della categoria."""
        if not self.nome_categoria or not self.nome_categoria.strip():
            raise ValueError("Il nome della categoria è obbligatorio")
        
        if not self.tipo_macro or not self.tipo_macro.strip():
            raise ValueError("Il tipo macro della categoria è obbligatorio")
        
        # Verifica che il tipo macro inizi con uno dei valori validi
        tipi_validi = [tipo.value for tipo in TipoMacroCategoria]
        tipo_base = self.tipo_macro.split(" ")[0]
        if tipo_base not in tipi_validi:
            raise ValueError(f"Il tipo macro deve iniziare con uno di: {', '.join(tipi_validi)}")
    
    def è_categoria_immobiliare(self) -> bool:
        """Verifica se la categoria è relativa a un immobile."""
        return self.tipo_macro.startswith(TipoMacroCategoria.IMMOBILE.value)
    
    def get_nome_proprieta_associata(self) -> Optional[str]:
        """
        Estrae il nome della proprietà se la categoria è immobiliare.
        
        Returns:
            str: Nome della proprietà, o None se non è categoria immobiliare
        """
        if self.è_categoria_immobiliare():
            # Rimuove "Immobile " dal tipo_macro per ottenere il nome proprietà
            return self.tipo_macro.replace(TipoMacroCategoria.IMMOBILE.value + " ", "")
        return None
    
    def __str__(self) -> str:
        return f"{self.nome_categoria} ({self.tipo_macro})"


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
    
    # Campi per riferimenti oggetto (non salvati in DB, usati in memoria)
    categoria: Optional[CategoriaTransazione] = field(default=None, init=False)
    conto: Optional[ContoFinanziario] = field(default=None, init=False)
    proprieta: Optional[Proprieta] = field(default=None, init=False)
    
    def __post_init__(self):
        """Validazione dei dati dopo l'inizializzazione."""
        self._valida()
    
    def _valida(self):
        """Esegue validazioni sui dati della transazione."""
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
        
        # Validazione data
        if self.data > date.today():
            raise ValueError("La data della transazione non può essere nel futuro")
    
    def è_entrata(self) -> bool:
        """Verifica se la transazione è un'entrata."""
        return self.importo > 0
    
    def è_uscita(self) -> bool:
        """Verifica se la transazione è un'uscita."""
        return self.importo < 0
    
    def get_importo_assoluto(self) -> float:
        """Restituisce l'importo in valore assoluto."""
        return abs(self.importo)
    
    def get_mese_anno(self) -> str:
        """Restituisce il mese e anno della transazione in formato MM/YYYY."""
        return self.data.strftime("%m/%Y")
    
    def get_anno(self) -> int:
        """Restituisce l'anno della transazione."""
        return self.data.year
    
    def to_dict_for_export(self) -> Dict:
        """
        Converte la transazione in dizionario per export.
        
        Returns:
            Dict con i dati della transazione formattati per export
        """
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


# Categorie predefinite per inizializzazione sistema
CATEGORIE_PREDEFINITE = [
    # Personali
    ("Stipendio Tirocinio", "Personale"),
    ("Cibo e Spesa", "Personale"),
    ("Trasporti", "Personale"),
    ("Tasse Scolastiche", "Personale"),
    ("Svago e Intrattenimento", "Personale"),
    ("Salute e Benessere", "Personale"),
    ("Abbigliamento", "Personale"),
    ("Tecnologia", "Personale"),
    ("Formazione", "Personale"),
    ("Altro Personale", "Personale"),
    
    # Fiscali Generali
    ("IRPEF", "Fiscale Generale"),
    ("Acconti Fiscali", "Fiscale Generale"),
    ("Commercialista", "Fiscale Generale"),
    ("Bolli e Imposte", "Fiscale Generale"),
    
    # Le categorie immobiliari verranno create dinamicamente per ogni proprietà
]


def crea_categorie_per_proprieta(nome_proprieta: str, tipo_proprieta: TipoProprieta) -> List[tuple]:
    """
    Crea le categorie standard per una nuova proprietà.
    
    Args:
        nome_proprieta: Nome identificativo della proprietà
        tipo_proprieta: Tipo di proprietà
        
    Returns:
        Lista di tuple (nome_categoria, tipo_macro) da creare
    """
    tipo_macro = f"Immobile {nome_proprieta}"
    categorie = []
    
    if tipo_proprieta == TipoProprieta.POSSESSO_AFFITTATA:
        categorie.append((f"Affitto Incassato {nome_proprieta}", tipo_macro))
    
    if tipo_proprieta in [TipoProprieta.POSSESSO_USO_PERSONALE, TipoProprieta.POSSESSO_AFFITTATA]:
        categorie.extend([
            (f"Mutuo/Rata {nome_proprieta}", tipo_macro),
            (f"IMU/TASI {nome_proprieta}", tipo_macro),
            (f"Manutenzione {nome_proprieta}", tipo_macro),
            (f"Utenze {nome_proprieta}", tipo_macro),
            (f"Spese Condominiali {nome_proprieta}", tipo_macro),
            (f"Assicurazione {nome_proprieta}", tipo_macro),
            (f"Altro {nome_proprieta}", tipo_macro),
        ])
    
    if tipo_proprieta == TipoProprieta.AFFITTO_PASSIVO:
        categorie.append((f"Affitto Pagato {nome_proprieta}", "Personale"))  # Va in Personale
        categorie.append((f"Spese Accessorie {nome_proprieta}", "Personale"))
    
    return categorie