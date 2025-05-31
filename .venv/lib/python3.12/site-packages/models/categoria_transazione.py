from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from .proprieta import TipoProprieta

class TipoMacroCategoria(Enum):
    """Enumerazione per i tipi macro di categoria transazione."""
    PERSONALE = "Personale"
    IMMOBILE = "Immobile"  # Seguito da nome proprietà, es: "Immobile Casa Via Rossi"
    FISCALE_GENERALE = "Fiscale Generale"

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
        self._valida()

    def _valida(self):
        if not self.nome_categoria or not self.nome_categoria.strip():
            raise ValueError("Il nome della categoria è obbligatorio")
        if not self.tipo_macro or not self.tipo_macro.strip():
            raise ValueError("Il tipo macro della categoria è obbligatorio")
        tipi_validi = [tipo.value for tipo in TipoMacroCategoria]
        tipo_base = self.tipo_macro.split(" ")[0]
        if tipo_base not in tipi_validi:
            raise ValueError(f"Il tipo macro deve iniziare con uno di: {', '.join(tipi_validi)}")

    def è_categoria_immobiliare(self) -> bool:
        return self.tipo_macro.startswith(TipoMacroCategoria.IMMOBILE.value)

    def get_nome_proprieta_associata(self) -> Optional[str]:
        if self.è_categoria_immobiliare():
            return self.tipo_macro.replace(TipoMacroCategoria.IMMOBILE.value + " ", "")
        return None

    def __str__(self) -> str:
        return f"{self.nome_categoria} ({self.tipo_macro})"

CATEGORIE_PREDEFINITE = [
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
    ("IRPEF", "Fiscale Generale"),
    ("Acconti Fiscali", "Fiscale Generale"),
    ("Commercialista", "Fiscale Generale"),
    ("Bolli e Imposte", "Fiscale Generale"),
]

def crea_categorie_per_proprieta(nome_proprieta: str, tipo_proprieta: TipoProprieta) -> List[tuple]:
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
        categorie.append((f"Affitto Pagato {nome_proprieta}", "Personale"))
        categorie.append((f"Spese Accessorie {nome_proprieta}", "Personale"))
    return categorie
