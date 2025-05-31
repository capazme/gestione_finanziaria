from typing import Dict, Optional
from src.repositories.conto_repository import ContoRepository
from src.repositories.transazione_repository import TransazioneRepository
from src.models.models import ContoFinanziario, Transazione
from src.database.database_connection import get_db_cursor

class SaldoCalculator:
    def __init__(self, conto_repo: Optional[ContoRepository] = None, transazione_repo: Optional[TransazioneRepository] = None):
        self.conto_repo = conto_repo or ContoRepository()
        self.transazione_repo = transazione_repo or TransazioneRepository()

    def ricalcola_e_aggiorna_saldo_conto(self, id_conto: int) -> ContoFinanziario:
        """
        Ricalcola il saldo attuale del conto partendo dal saldo iniziale e sommando tutte le transazioni associate.
        Aggiorna il saldo_attuale nel database in modo atomico.
        """
        with get_db_cursor():
            conto = self.conto_repo.get_by_id(id_conto)
            if not conto:
                raise ValueError(f"Conto con ID {id_conto} non trovato")
            transazioni = self.transazione_repo.get_by_conto_id(id_conto)
            saldo = conto.saldo_iniziale
            for t in transazioni:
                saldo += t.importo
            conto.saldo_attuale = round(saldo, 2)
            self.conto_repo.update(conto)
            return conto

    def aggiorna_saldo_dopo_modifica_transazione(self, transazione: Transazione, operazione: str, transazione_precedente: Optional[Transazione] = None):
        """
        Aggiorna i saldi dei conti dopo una modifica a una transazione.
        operazione: 'create', 'update', 'delete'
        transazione_precedente: necessario per update se cambia conto
        """
        if operazione == 'create':
            self.ricalcola_e_aggiorna_saldo_conto(transazione.id_conto_finanziario)
        elif operazione == 'delete':
            self.ricalcola_e_aggiorna_saldo_conto(transazione.id_conto_finanziario)
        elif operazione == 'update':
            # Se cambia conto, aggiorna entrambi
            if transazione_precedente and transazione_precedente.id_conto_finanziario != transazione.id_conto_finanziario:
                self.ricalcola_e_aggiorna_saldo_conto(transazione_precedente.id_conto_finanziario)
                self.ricalcola_e_aggiorna_saldo_conto(transazione.id_conto_finanziario)
            else:
                self.ricalcola_e_aggiorna_saldo_conto(transazione.id_conto_finanziario)
        else:
            raise ValueError("Operazione non supportata. Usa 'create', 'update' o 'delete'.")

    def verifica_coerenza_saldi_tutti_conti(self) -> Dict[int, bool]:
        """
        Verifica la coerenza tra saldo_attuale e saldo calcolato per tutti i conti.
        Restituisce un dizionario {id_conto: True/False}.
        """
        risultati = {}
        conti = self.conto_repo.get_all()
        for conto in conti:
            transazioni = self.transazione_repo.get_by_conto_id(conto.id_conto)
            saldo_calcolato = conto.saldo_iniziale
            for t in transazioni:
                saldo_calcolato += t.importo
            saldo_calcolato = round(saldo_calcolato, 2)
            risultati[conto.id_conto] = (saldo_calcolato == round(conto.saldo_attuale or 0, 2))
        return risultati
