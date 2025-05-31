from typing import Optional, Dict, List
from datetime import date, datetime, timedelta
from src.repositories.transazione_repository import TransazioneRepository
from src.repositories.proprieta_repository import ProprietaRepository
from src.repositories.categoria_repository import CategoriaRepository
from src.repositories.conto_repository import ContoRepository
from src.models.models import TipoFlusso, TipoProprieta

class ReportGenerator:
    def __init__(self,
                 transazione_repo: Optional[TransazioneRepository] = None,
                 proprieta_repo: Optional[ProprietaRepository] = None,
                 categoria_repo: Optional[CategoriaRepository] = None,
                 conto_repo: Optional[ContoRepository] = None):
        self.transazione_repo = transazione_repo or TransazioneRepository()
        self.proprieta_repo = proprieta_repo or ProprietaRepository()
        self.categoria_repo = categoria_repo or CategoriaRepository()
        self.conto_repo = conto_repo or ContoRepository()

    def generate_cash_flow_personale(self, anno: int, mese: Optional[int] = None) -> Dict:
        if mese:
            data_inizio = date(anno, mese, 1)
            if mese == 12:
                data_fine = date(anno, 12, 31)
            else:
                data_fine = date(anno, mese + 1, 1) - timedelta(days=1)
            periodo_str = data_inizio.strftime("%B %Y")
        else:
            data_inizio = date(anno, 1, 1)
            data_fine = date(anno, 12, 31)
            periodo_str = f"Anno {anno}"
        transazioni = self.transazione_repo.get_by_tipo_flusso(TipoFlusso.PERSONALE, data_inizio, data_fine)
        totale_entrate = sum(t.importo for t in transazioni if t.importo > 0)
        totale_uscite = -sum(t.importo for t in transazioni if t.importo < 0)
        risparmio = totale_entrate - totale_uscite
        return {
            "periodo": periodo_str,
            "totale_entrate_personali": round(totale_entrate, 2),
            "totale_uscite_personali": round(totale_uscite, 2),
            "risparmio_deficit_personale": round(risparmio, 2)
        }

    def generate_pl_proprieta(self, id_proprieta: int, anno: int, mese: Optional[int] = None) -> Dict:
        prop = self.proprieta_repo.get_by_id(id_proprieta)
        if not prop:
            raise ValueError(f"Proprietà con ID {id_proprieta} non trovata")
        if mese:
            data_inizio = date(anno, mese, 1)
            if mese == 12:
                data_fine = date(anno, 12, 31)
            else:
                data_fine = date(anno, mese + 1, 1) - timedelta(days=1)
            periodo_str = data_inizio.strftime("%B %Y")
        else:
            data_inizio = date(anno, 1, 1)
            data_fine = date(anno, 12, 31)
            periodo_str = f"Anno {anno}"
        if prop.tipo == TipoProprieta.POSSESSO_AFFITTATA:
            entrate = self.transazione_repo.get_entrate_da_affitto_per_proprieta(id_proprieta, data_inizio, data_fine)
            totale_affitti = sum(t.importo for t in entrate)
        else:
            totale_affitti = 0.0
        transazioni = self.transazione_repo.get_by_proprieta_id(id_proprieta, data_inizio, data_fine)
        totale_spese = -sum(t.importo for t in transazioni if t.importo < 0)
        profit_loss = totale_affitti - totale_spese
        return {
            "nome_proprieta": prop.nome_o_indirizzo_breve,
            "periodo": periodo_str,
            "tipo_proprieta": prop.tipo.value,
            "totale_affitti_incassati": round(totale_affitti, 2) if prop.tipo == TipoProprieta.POSSESSO_AFFITTATA else None,
            "totale_spese_proprieta": round(totale_spese, 2),
            "profit_loss_netto": round(profit_loss, 2)
        }

    def generate_riepilogo_fiscale(self, anno: int) -> Dict:
        data_inizio = date(anno, 1, 1)
        data_fine = date(anno, 12, 31)
        trans_deducibili = self.transazione_repo.get_fiscalmente_rilevanti(data_inizio, data_fine)
        elenco = []
        for t in trans_deducibili:
            # Recupera nome categoria
            cat = self.categoria_repo.get_by_id(t.id_categoria)
            elenco.append({
                "data": t.data.strftime("%Y-%m-%d"),
                "descrizione": t.descrizione,
                "importo": t.importo,
                "categoria": cat.nome_categoria if cat else f"ID: {t.id_categoria}"
            })
        somma_totale = sum(t.importo for t in trans_deducibili)
        # Riepilogo entrate da affitto per proprietà
        riepilogo_affitti = {}
        props = self.proprieta_repo.get_by_tipo(TipoProprieta.POSSESSO_AFFITTATA)
        totale_affitti = 0.0
        for p in props:
            entrate = self.transazione_repo.get_entrate_da_affitto_per_proprieta(p.id_proprieta, data_inizio, data_fine)
            totale = sum(t.importo for t in entrate)
            riepilogo_affitti[p.nome_o_indirizzo_breve] = round(totale, 2)
            totale_affitti += totale
        return {
            "anno": anno,
            "elenco_transazioni_deducibili": elenco,
            "somma_totale_deducibili": round(somma_totale, 2),
            "riepilogo_entrate_da_affitto_per_proprieta": riepilogo_affitti,
            "totale_entrate_da_affitto": round(totale_affitti, 2)
        }

    def calculate_patrimonio_netto_semplificato(self) -> Dict:
        props = self.proprieta_repo.get_all()
        somma_valori = sum(p.valore_acquisto_o_stima_attuale or 0 for p in props if p.tipo in [TipoProprieta.POSSESSO_AFFITTATA, TipoProprieta.POSSESSO_USO_PERSONALE])
        conti = self.conto_repo.get_all()
        somma_saldi = sum(c.saldo_attuale or 0 for c in conti)
        patrimonio = somma_valori + somma_saldi
        return {
            "data_calcolo": datetime.now().isoformat(timespec='seconds'),
            "somma_valori_proprieta": round(somma_valori, 2),
            "somma_saldi_conti_attivi": round(somma_saldi, 2),
            "patrimonio_netto_semplificato": round(patrimonio, 2)
        }
