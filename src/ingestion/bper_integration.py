"""
Script di integrazione tra il parser BPER e il sistema di gestione finanziaria.
Importa automaticamente le transazioni dall'estratto conto nel database.
"""

import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional

# Aggiungi path per importare i moduli del sistema
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.ingestion.bper_parser_improved import BPERParser
from src.models.conto_finanziario import (
    ContoFinanziario,
    TipoConto
)
from src.models.categoria_transazione import CategoriaTransazione
from src.database.database_connection import init_database, get_db_cursor
from src.repositories.conto_repository import ContoRepository
from src.repositories.categoria_repository import CategoriaRepository
from src.repositories.transazione_repository import TransazioneRepository
from src.services.saldo_calculator import SaldoCalculator
from src.models.transazione import TipoFlusso


class BPERImporter:
    """Importa transazioni da estratti conto BPER nel sistema di gestione finanziaria."""
    
    def __init__(self):
        self.parser = BPERParser()
        self.conto_repo = ContoRepository()
        self.categoria_repo = CategoriaRepository()
        self.transazione_repo = TransazioneRepository()
        self.saldo_calculator = SaldoCalculator()
        
        # Mapping categorie BPER -> categorie sistema
        self.categoria_mapping = {
            'Affitto': 'Affitto Incassato',
            'Stipendio': 'Stipendio Tirocinio',
            'Utenze': 'Utenze Casa',
            'PayPal': 'Acquisti Online',
            'Commissioni': 'Commissioni Bancarie',
            'Prelievo': 'Prelievo Contanti',
            'Spesa Alimentari': 'Cibo e Spesa',
            'Trasporti': 'Trasporti',
            'Ristorazione': 'Svago e Intrattenimento',
            'Salute': 'Salute e Benessere',
            'Shopping': 'Shopping',
            'Carburante': 'Trasporti',
            'Servizi': 'Servizi Digitali',
            'Altro': 'Altro Personale'
        }
    
    def import_from_pdf(self, pdf_path: str, conto_id: Optional[int] = None) -> Dict:
        """
        Importa transazioni da un PDF BPER.
        
        Args:
            pdf_path: Percorso del file PDF
            conto_id: ID del conto nel sistema (se None, cerca o crea)
            
        Returns:
            Dizionario con risultati dell'importazione
        """
        print(f"\n=== IMPORTAZIONE ESTRATTO CONTO BPER ===")
        print(f"File: {pdf_path}")
        
        # 1. Parse del PDF
        print("\n1. Parsing del PDF...")
        data = self.parser.parse(pdf_path)
        print(f"   ✓ Trovate {len(data['transazioni'])} transazioni")
        
        # 2. Verifica/crea conto
        print("\n2. Verifica conto bancario...")
        conto = self._get_or_create_conto(data['info_conto'], conto_id)
        print(f"   ✓ Conto: {conto.nome_conto} (ID: {conto.id_conto})")
        
        # 3. Verifica/crea categorie
        print("\n3. Verifica categorie...")
        categoria_map = self._ensure_categories()
        print(f"   ✓ {len(categoria_map)} categorie disponibili")
        
        # 4. Importa transazioni
        print("\n4. Importazione transazioni...")
        risultati = self._import_transactions(
            data['transazioni'], 
            conto.id_conto, 
            categoria_map
        )
        
        # 5. Aggiorna saldo conto
        print("\n5. Aggiornamento saldo conto...")
        nuovo_saldo = self._update_account_balance(conto, data['riepilogo'])
        print(f"   ✓ Nuovo saldo: €{nuovo_saldo:.2f}")
        
        # 6. Genera report
        risultati['conto'] = conto
        risultati['riepilogo_pdf'] = data['riepilogo']
        risultati['statistiche'] = data['statistiche']
        
        self._print_import_summary(risultati)
        
        return risultati
    
    def _get_or_create_conto(self, info_conto: Dict, conto_id: Optional[int]) -> ContoFinanziario:
        """Recupera o crea il conto bancario."""
        if conto_id:
            # Usa conto specificato
            conto = self.conto_repo.get_by_id(conto_id)
            if not conto:
                raise ValueError(f"Conto con ID {conto_id} non trovato")
            return conto
        
        # Cerca per IBAN
        iban = info_conto.get('iban')
        if iban:
            # Cerca nelle note o nel nome
            conti = self.conto_repo.get_all()
            for c in conti:
                if iban in c.nome_conto or (hasattr(c, 'note') and iban in str(c.note)):
                    return c
        
        # Crea nuovo conto
        nome_conto = f"BPER - {info_conto.get('filiale', 'Conto')}"
        if iban:
            nome_conto += f" ({iban[-4:]})"
        
        nuovo_conto = ContoFinanziario(
            nome_conto=nome_conto,
            tipo_conto=TipoConto.BANCARIO,
            saldo_iniziale=0  # Verrà aggiornato dopo
        )
        
        return self.conto_repo.create(nuovo_conto)
    
    def _ensure_categories(self) -> Dict[str, int]:
        """Assicura che tutte le categorie necessarie esistano."""
        categoria_map = {}
        
        # Recupera categorie esistenti
        categorie_esistenti = self.categoria_repo.get_all()
        for cat in categorie_esistenti:
            categoria_map[cat.nome_categoria] = cat.id_categoria
        
        # Crea categorie mancanti
        for cat_bper, cat_sistema in self.categoria_mapping.items():
            if cat_sistema not in categoria_map:
                tipo_macro = "Personale"
                print(f"Creo categoria: {cat_sistema} - tipo_macro: {tipo_macro}")
                nuova_cat = CategoriaTransazione(
                    nome_categoria=cat_sistema,
                    tipo_macro=tipo_macro
                )
                try:
                    cat_creata = self.categoria_repo.create(nuova_cat)
                    categoria_map[cat_sistema] = cat_creata.id_categoria
                except ValueError:
                    # Categoria già esistente
                    pass
        
        return categoria_map
    
    def _import_transactions(self, transazioni: List[Dict], 
                           conto_id: int, 
                           categoria_map: Dict[str, int]) -> Dict:
        """Importa le transazioni nel database."""
        risultati = {
            'importate': 0,
            'duplicate': 0,
            'errori': 0,
            'dettagli_errori': []
        }
        
        for trans_data in transazioni:
            try:
                # Verifica se già esiste
                if self._transaction_exists(trans_data, conto_id):
                    risultati['duplicate'] += 1
                    continue
                
                # Determina categoria
                cat_suggerita = trans_data.get('categoria_suggerita', 'Altro')
                cat_sistema = self.categoria_mapping.get(cat_suggerita, 'Altro Personale')
                id_categoria = categoria_map.get(cat_sistema, 
                                               categoria_map.get('Altro Personale', 1))
                
                # Determina tipo flusso
                tipo_flusso = self._determine_tipo_flusso(trans_data['descrizione'])
                
                # Crea transazione
                transazione = Transazione(
                    data=trans_data['data_transazione'],
                    importo=trans_data['importo'],
                    descrizione=trans_data['descrizione'][:200],  # Limita lunghezza
                    id_categoria=id_categoria,
                    id_conto_finanziario=conto_id,
                    tipo_flusso=tipo_flusso,
                    flag_deducibile_o_rilevante_fiscalmente=self._is_deducibile(
                        trans_data['descrizione'], 
                        cat_sistema
                    ),
                    note_aggiuntive=f"Importato da BPER - Data valuta: {trans_data['data_valuta']}"
                )
                
                self.transazione_repo.create(transazione)
                risultati['importate'] += 1
                
                # Progress
                if risultati['importate'] % 10 == 0:
                    print(f"   ... {risultati['importate']} transazioni importate")
                
            except Exception as e:
                risultati['errori'] += 1
                risultati['dettagli_errori'].append({
                    'transazione': trans_data,
                    'errore': str(e)
                })
        
        return risultati
    
    def _transaction_exists(self, trans_data: Dict, conto_id: int) -> bool:
        """Verifica se una transazione esiste già (per evitare duplicati)."""
        # Cerca transazioni simili nella stessa data
        transazioni_esistenti = self.transazione_repo.get_by_date_range(
            trans_data['data_transazione'],
            trans_data['data_transazione'],
            conto_id
        )
        
        for trans in transazioni_esistenti:
            # Confronta importo e parte della descrizione
            if (abs(trans.importo - trans_data['importo']) < 0.01 and
                trans_data['descrizione'][:30] in trans.descrizione):
                return True
        
        return False
    
    def _determine_tipo_flusso(self, descrizione: str) -> TipoFlusso:
        """Determina il tipo di flusso dalla descrizione."""
        desc_lower = descrizione.lower()
        
        if any(word in desc_lower for word in ['affitto', 'canone', 'locazione']):
            return TipoFlusso.IMMOBILIARE
        elif any(word in desc_lower for word in ['irpef', 'f24', 'agenzia entrate']):
            return TipoFlusso.FISCALE
        else:
            return TipoFlusso.PERSONALE
    
    def _is_deducibile(self, descrizione: str, categoria: str) -> bool:
        """Determina se una transazione è deducibile fiscalmente."""
        desc_lower = descrizione.lower()
        
        # Categorie sempre deducibili
        categorie_deducibili = [
            'Salute e Benessere',
            'Tasse Scolastiche',
            'Formazione'
        ]
        
        if categoria in categorie_deducibili:
            return True
        
        # Parole chiave per deducibilità
        parole_deducibili = [
            'farmacia', 'medico', 'dottore', 'analisi',
            'università', 'tasse', 'irpef', 'f24'
        ]
        
        return any(word in desc_lower for word in parole_deducibili)
    
    def _update_account_balance(self, conto: ContoFinanziario, 
                              riepilogo: Dict) -> float:
        """Aggiorna il saldo del conto basandosi sull'estratto."""
        # Usa il calcolatore per ricalcolare il saldo
        nuovo_saldo = self.saldo_calculator.calcola_saldo_conto(conto.id_conto)
        
        # Verifica con saldo finale dell'estratto
        saldo_estratto = riepilogo.get('saldo_finale', {}).get('importo', 0)
        
        if abs(nuovo_saldo - saldo_estratto) > 0.01:
            print(f"   ⚠️  Attenzione: differenza tra saldo calcolato ({nuovo_saldo:.2f}) "
                  f"e saldo estratto ({saldo_estratto:.2f})")
        
        return nuovo_saldo
    
    def _print_import_summary(self, risultati: Dict):
        """Stampa un riepilogo dell'importazione."""
        print("\n=== RIEPILOGO IMPORTAZIONE ===")
        print(f"Transazioni importate: {risultati['importate']}")
        print(f"Transazioni duplicate: {risultati['duplicate']}")
        print(f"Errori: {risultati['errori']}")
        
        if risultati['errori'] > 0:
            print("\nErrori riscontrati:")
            for err in risultati['dettagli_errori'][:5]:  # Mostra max 5 errori
                print(f"- {err['transazione']['data_transazione']}: {err['errore']}")
        
        # Statistiche
        stats = risultati.get('statistiche', {})
        if stats:
            print("\n=== ANALISI SPESE PERIODO ===")
            categorie = stats.get('categorie', {})
            
            # Ordina per spesa totale (negativa)
            spese_ordinate = sorted(
                [(cat, info) for cat, info in categorie.items() if info['totale'] < 0],
                key=lambda x: x[1]['totale']
            )
            
            for cat, info in spese_ordinate[:10]:  # Top 10 categorie di spesa
                print(f"{cat:25} €{abs(info['totale']):>10.2f} ({info['numero']:>3} trans.)")


def interactive_import():
    """Importazione interattiva con menu."""
    print("\n=== IMPORTAZIONE ESTRATTO CONTO BPER ===")
    
    # Verifica file PDF
    pdf_files = list(Path('.').glob('*.pdf'))
    if not pdf_files:
        print("Nessun file PDF trovato nella directory corrente.")
        pdf_path = input("Inserisci il percorso del file PDF: ")
    else:
        print("\nFile PDF trovati:")
        for i, f in enumerate(pdf_files, 1):
            print(f"{i}. {f.name}")
        
        scelta = input("\nSeleziona file (numero) o inserisci percorso: ")
        if scelta.isdigit() and 1 <= int(scelta) <= len(pdf_files):
            pdf_path = str(pdf_files[int(scelta) - 1])
        else:
            pdf_path = scelta
    
    # Verifica conto
    print("\nVuoi selezionare un conto esistente? (s/n): ", end='')
    if input().lower() == 's':
        # Mostra conti esistenti
        conto_repo = ContoRepository()
        conti = conto_repo.get_all()
        
        if conti:
            print("\nConti disponibili:")
            for c in conti:
                print(f"{c.id_conto}. {c.nome_conto} - Saldo: €{c.saldo_attuale:.2f}")
            
            conto_id = int(input("\nID conto: "))
        else:
            print("Nessun conto trovato. Verrà creato automaticamente.")
            conto_id = None
    else:
        conto_id = None
    
    # Esegui importazione
    importer = BPERImporter()
    try:
        risultati = importer.import_from_pdf(pdf_path, conto_id)
        
        # Chiedi se generare report
        print("\n\nVuoi generare un report dettagliato? (s/n): ", end='')
        if input().lower() == 's':
            from services.report_generator import ReportGenerator
            generator = ReportGenerator()
            
            # Estrai periodo dal PDF
            periodo_inizio = risultati['riepilogo_pdf']['saldo_iniziale']['data']
            periodo_fine = risultati['riepilogo_pdf']['saldo_finale']['data']
            
            print(f"\nGenerazione report per periodo {periodo_inizio} - {periodo_fine}...")
            
            # Genera cash flow del periodo
            cash_flow = generator.generate_cash_flow_personale(
                periodo_inizio.month,
                periodo_inizio.year
            )
            
            print("\n=== CASH FLOW PERSONALE ===")
            print(f"Entrate: €{cash_flow['totale_entrate']:.2f}")
            print(f"Uscite: €{cash_flow['totale_uscite']:.2f}")
            print(f"Risparmio: €{cash_flow['risparmio']:.2f}")
            
    except Exception as e:
        print(f"\nErrore durante l'importazione: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Inizializza database se necessario
    init_database()
    
    # Avvia importazione interattiva
    interactive_import()