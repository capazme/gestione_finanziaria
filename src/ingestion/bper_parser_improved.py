import pdfplumber
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BPERParser:
    """Parser migliorato per estratti conto BPER."""
    
    def __init__(self):
        # Pattern regex ottimizzati per il formato BPER
        self.patterns = {
            'iban': r'IBAN\s+([A-Z]{2}\s*\d{2}\s*[A-Z]\s*\d{5}\s*\d{5}\s*\d+)',
            'saldo_iniziale': r'Saldo iniziale al\s*(\d{2}/\d{2}/\d{4})\s*([\d.,]+)\s*€',
            'saldo_finale': r'Saldo finale al\s*(\d{2}/\d{2}/\d{4})\s*([\d.,]+)\s*€',
            'totale_entrate': r'Totale Entrate\s*([\d.,]+)\s*€',
            'totale_uscite': r'Totale Uscite\s*([\d.,]+)\s*€',
            'data_transazione': r'^(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})',
            'importo': r'([\d.,]+)',
            'isee_giacenza': r'Giacenza media ai\s*fini ISEE\s*([\d.,]+)\s*€',
            'isee_saldo_fine': r'Saldo al\s*31/12/\d{4}\s*([\d.,]+)\s*€'
        }
    
    def parse(self, pdf_path: str) -> Dict:
        """
        Parse completo dell'estratto conto BPER.
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            Dizionario con tutti i dati estratti
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Estrai testo da tutte le pagine
                all_text = ""
                page_texts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                        page_texts.append(text)
                
                # Estrai informazioni
                result = {
                    "info_conto": self._extract_account_info(all_text),
                    "transazioni": self._extract_all_transactions(page_texts),
                    "riepilogo": self._extract_summary(all_text),
                    "info_isee": self._extract_isee_info(all_text),
                    "interessi": self._extract_interests(page_texts)
                }
                
                # Calcola statistiche
                result["statistiche"] = self._calculate_statistics(result["transazioni"])
                
                return result
                
        except Exception as e:
            logger.error(f"Errore nel parsing del PDF: {e}")
            raise
    
    def _extract_account_info(self, text: str) -> Dict:
        """Estrai informazioni generali del conto."""
        info = {}
        
        # IBAN
        iban_match = re.search(self.patterns['iban'], text)
        if iban_match:
            info['iban'] = iban_match.group(1).replace(' ', '')
        
        # BIC
        bic_match = re.search(r'BIC\s+([A-Z0-9\s]+XXX)', text)
        if bic_match:
            info['bic'] = bic_match.group(1).strip()
        
        # Intestatario
        intestatario_match = re.search(r'(PUZIO GUGLIELMO[\s\S]*?)(?=Riepilogo|Coordinate)', text)
        if intestatario_match:
            lines = intestatario_match.group(1).strip().split('\n')
            info['intestatario'] = {
                'nome': lines[0].strip(),
                'indirizzo': ' '.join(lines[1:3]).strip() if len(lines) > 2 else ''
            }
        
        # Filiale
        filiale_match = re.search(r'(?:Filiale|presso)\s+([A-Z\-]+)', text)
        if filiale_match:
            info['filiale'] = filiale_match.group(1)
        
        return info
    
    def _extract_summary(self, text: str) -> Dict:
        """Estrai il riepilogo del conto."""
        summary = {}
        
        # Saldo iniziale
        saldo_init = re.search(self.patterns['saldo_iniziale'], text)
        if saldo_init:
            summary['saldo_iniziale'] = {
                'data': self._parse_date(saldo_init.group(1)),
                'importo': self._parse_amount(saldo_init.group(2))
            }
        
        # Saldo finale
        saldo_fin = re.search(self.patterns['saldo_finale'], text)
        if saldo_fin:
            summary['saldo_finale'] = {
                'data': self._parse_date(saldo_fin.group(1)),
                'importo': self._parse_amount(saldo_fin.group(2))
            }
        
        # Totali
        tot_entrate = re.search(self.patterns['totale_entrate'], text)
        if tot_entrate:
            summary['totale_entrate'] = self._parse_amount(tot_entrate.group(1))
        
        tot_uscite = re.search(self.patterns['totale_uscite'], text)
        if tot_uscite:
            summary['totale_uscite'] = self._parse_amount(tot_uscite.group(1))
        
        # Calcola variazione
        if 'saldo_iniziale' in summary and 'saldo_finale' in summary:
            summary['variazione'] = round(
                summary['saldo_finale']['importo'] - summary['saldo_iniziale']['importo'], 2
            )
        
        return summary
    
    def _extract_all_transactions(self, page_texts: List[str]) -> List[Dict]:
        """Estrai tutte le transazioni da tutte le pagine."""
        all_transactions = []
        
        for page_num, page_text in enumerate(page_texts, 1):
            transactions = self._extract_transactions_from_page(page_text, page_num)
            all_transactions.extend(transactions)
        
        # Ordina per data
        all_transactions.sort(key=lambda x: x['data_transazione'])
        
        # Aggiungi numerazione progressiva
        for i, trans in enumerate(all_transactions, 1):
            trans['numero_progressivo'] = i
        
        return all_transactions
    
    def _extract_transactions_from_page(self, page_text: str, page_num: int) -> List[Dict]:
        """Estrai transazioni da una singola pagina."""
        transactions = []
        lines = page_text.split('\n')
        
        # Trova l'inizio della tabella movimenti
        start_idx = -1
        for i, line in enumerate(lines):
            if re.search(r'DATA\s+VALUTA\s+USCITE\s+ENTRATE\s+DESCRIZIONE', line):
                start_idx = i + 1
                break
        
        if start_idx == -1:
            return transactions
        
        # Trova fine tabella (prima di "Dati da utilizzare" o fine pagina)
        end_idx = len(lines)
        for i in range(start_idx, len(lines)):
            if 'Dati da utilizzare' in lines[i] or 'Mod. 05.13.0011' in lines[i]:
                end_idx = i
                break
        
        # Processa le righe di transazione
        current_transaction = None
        
        for i in range(start_idx, end_idx):
            line = lines[i].strip()
            
            if not line:
                continue
            
            # Controlla se è una riga SALDO (iniziale o finale)
            if re.match(r'\d{2}/\d{2}/\d{2}\s+[\d.,]+\s+SALDO', line):
                continue
            
            # Controlla se è l'inizio di una nuova transazione
            date_match = re.match(r'^(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})\s+(.+)', line)
            
            if date_match:
                # Salva la transazione precedente se esiste
                if current_transaction:
                    transactions.append(current_transaction)
                
                # Inizia nuova transazione
                data_trans = date_match.group(1)
                data_valuta = date_match.group(2)
                resto_riga = date_match.group(3)
                
                # Estrai importi e descrizione dal resto della riga
                trans_data = self._parse_transaction_amounts(resto_riga)
                
                current_transaction = {
                    'data_transazione': self._parse_date_short(data_trans),
                    'data_valuta': self._parse_date_short(data_valuta),
                    'importo_uscita': trans_data['uscita'],
                    'importo_entrata': trans_data['entrata'],
                    'importo': trans_data['importo_netto'],
                    'descrizione': trans_data['descrizione'],
                    'tipo_movimento': 'ENTRATA' if trans_data['importo_netto'] > 0 else 'USCITA',
                    'pagina': page_num
                }
            
            elif current_transaction and line:
                # Continua la descrizione della transazione corrente
                current_transaction['descrizione'] += ' ' + line
        
        # Non dimenticare l'ultima transazione
        if current_transaction:
            transactions.append(current_transaction)
        
        # Pulisci le descrizioni
        for trans in transactions:
            trans['descrizione'] = self._clean_description(trans['descrizione'])
            trans['categoria_suggerita'] = self._suggest_category(trans['descrizione'])
        
        return transactions
    
    def _parse_transaction_amounts(self, line: str) -> Dict:
        """Parse degli importi e descrizione da una riga di transazione."""
        # Pattern per trovare importi (numero con virgola e opzionalmente punto per migliaia)
        amount_pattern = r'([\d.]+,\d{2})'
        amounts = re.findall(amount_pattern, line)
        
        # Rimuovi gli importi dalla riga per ottenere la descrizione
        description = line
        for amount in amounts:
            description = description.replace(amount, '', 1)
        
        # Determina uscita/entrata basandosi sulla posizione
        uscita = None
        entrata = None
        
        if len(amounts) >= 1:
            # Il primo importo trovato potrebbe essere uscita o entrata
            # Dobbiamo determinarlo dal contesto
            first_amount_pos = line.find(amounts[0])
            
            # Se c'è molto spazio prima del primo importo, probabilmente è un'entrata
            if first_amount_pos > 20:
                entrata = self._parse_amount(amounts[0])
            else:
                uscita = self._parse_amount(amounts[0])
                if len(amounts) >= 2:
                    entrata = self._parse_amount(amounts[1])
        
        # Calcola importo netto
        importo_netto = 0
        if entrata:
            importo_netto = entrata
        elif uscita:
            importo_netto = -uscita
        
        return {
            'uscita': uscita,
            'entrata': entrata,
            'importo_netto': importo_netto,
            'descrizione': description.strip()
        }
    
    def _clean_description(self, description: str) -> str:
        """Pulisce la descrizione rimuovendo spazi extra e caratteri non necessari."""
        # Rimuovi spazi multipli
        description = re.sub(r'\s+', ' ', description)
        
        # Rimuovi numeri di riferimento molto lunghi alla fine
        description = re.sub(r'-RIF\.\s*\d+/\d+$', '', description)
        
        return description.strip()
    
    def _suggest_category(self, description: str) -> str:
        """Suggerisce una categoria basata sulla descrizione."""
        description_lower = description.lower()
        
        categories = {
            'Affitto': ['affitto', 'canone affitto', 'fitto'],
            'Stipendio': ['stipendio', 'bonifico o/c', 'bonifico sepa'],
            'Utenze': ['italia power', 'gas', 'luce', 'energia'],
            'PayPal': ['paypal'],
            'Commissioni': ['commissioni', 'canone mensile', 'spese su prelievo'],
            'Prelievo': ['prel. atm', 'prelievo atm'],
            'Spesa Alimentari': ['supermercato', 'conad'],
            'Trasporti': ['atac', 'trenitalia', 'unicocampania'],
            'Ristorazione': ['bar', 'caffetterie', 'pizzeria', 'ristorante'],
            'Salute': ['farmacia', 'diagnostica'],
            'Shopping': ['libraccio', 'klarna'],
            'Carburante': ['stazione energas'],
            'Servizi': ['glovo', 'sharenow']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        return 'Altro'
    
    def _extract_isee_info(self, text: str) -> Dict:
        """Estrai informazioni ISEE."""
        isee_info = {}
        
        # Cerca la sezione ISEE
        isee_section = re.search(
            r'Dati da utilizzare.*?ISEE.*?Giacenza media.*?([\d.,]+)\s*€',
            text,
            re.DOTALL
        )
        
        if isee_section:
            isee_info['giacenza_media'] = self._parse_amount(isee_section.group(1))
        
        # Saldo al 31/12
        saldo_match = re.search(
            r'Saldo al\s*31/12/(\d{4})\s*([\d.,]+)\s*€',
            text
        )
        if saldo_match:
            isee_info['anno'] = int(saldo_match.group(1))
            isee_info['saldo_fine_anno'] = self._parse_amount(saldo_match.group(2))
        
        return isee_info
    
    def _extract_interests(self, page_texts: List[str]) -> Dict:
        """Estrai informazioni su interessi creditori/debitori."""
        interests = {
            'creditori': [],
            'debitori': [],
            'totale_creditori': 0,
            'totale_debitori': 0
        }
        
        for page_text in page_texts:
            # Interessi creditori
            if 'INTERESSI CREDITORI MATURATI' in page_text:
                cred_match = re.findall(
                    r'(\d{2}/\d{2}/\d{2})\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
                    page_text
                )
                for match in cred_match:
                    if len(match) == 4:
                        interests['creditori'].append({
                            'data': self._parse_date_short(match[0]),
                            'tasso': float(match[1].replace(',', '.')),
                            'numeri': float(match[2].replace('.', '').replace(',', '.')),
                            'interessi': float(match[3].replace(',', '.'))
                        })
            
            # Totale interessi
            totale_match = re.search(r'TOTALE NETTO\s+([\d.,]+)', page_text)
            if totale_match:
                interests['totale_creditori'] = self._parse_amount(totale_match.group(1))
        
        return interests
    
    def _calculate_statistics(self, transactions: List[Dict]) -> Dict:
        """Calcola statistiche sulle transazioni."""
        if not transactions:
            return {}
        
        stats = {
            'numero_transazioni': len(transactions),
            'numero_entrate': sum(1 for t in transactions if t['importo'] > 0),
            'numero_uscite': sum(1 for t in transactions if t['importo'] < 0),
            'totale_entrate': sum(t['importo'] for t in transactions if t['importo'] > 0),
            'totale_uscite': abs(sum(t['importo'] for t in transactions if t['importo'] < 0)),
            'saldo_movimento': sum(t['importo'] for t in transactions),
            'media_entrate': 0,
            'media_uscite': 0,
            'max_entrata': 0,
            'max_uscita': 0,
            'categorie': {}
        }
        
        # Calcola medie
        if stats['numero_entrate'] > 0:
            stats['media_entrate'] = round(stats['totale_entrate'] / stats['numero_entrate'], 2)
            stats['max_entrata'] = max(t['importo'] for t in transactions if t['importo'] > 0)
        
        if stats['numero_uscite'] > 0:
            stats['media_uscite'] = round(stats['totale_uscite'] / stats['numero_uscite'], 2)
            stats['max_uscita'] = abs(min(t['importo'] for t in transactions if t['importo'] < 0))
        
        # Statistiche per categoria
        for trans in transactions:
            cat = trans.get('categoria_suggerita', 'Altro')
            if cat not in stats['categorie']:
                stats['categorie'][cat] = {
                    'numero': 0,
                    'totale': 0,
                    'transazioni': []
                }
            stats['categorie'][cat]['numero'] += 1
            stats['categorie'][cat]['totale'] += trans['importo']
            stats['categorie'][cat]['transazioni'].append(trans['numero_progressivo'])
        
        return stats
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse data in formato DD/MM/YYYY."""
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
            return None
    
    def _parse_date_short(self, date_str: str) -> Optional[date]:
        """Parse data in formato DD/MM/YY."""
        try:
            # Assumi che 00-30 sia 2000-2030, 31-99 sia 1931-1999
            dt = datetime.strptime(date_str, '%d/%m/%y')
            if dt.year > 2030:
                dt = dt.replace(year=dt.year - 100)
            return dt.date()
        except:
            return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse importo in formato italiano (. per migliaia, , per decimali)."""
        if not amount_str or not amount_str.strip():
            return 0.0
        
        # Rimuovi spazi e simbolo euro
        amount_str = amount_str.strip().replace('€', '').strip()
        
        # Sostituisci . con niente (separatore migliaia) e , con . (decimali)
        amount_str = amount_str.replace('.', '').replace(',', '.')
        
        try:
            return float(amount_str)
        except:
            return 0.0


def export_to_csv(data: Dict, output_file: str = 'transazioni_bper.csv'):
    """Esporta le transazioni in formato CSV."""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'numero_progressivo', 'data_transazione', 'data_valuta',
            'importo', 'tipo_movimento', 'categoria_suggerita', 
            'descrizione', 'pagina'
        ])
        writer.writeheader()
        
        for trans in data['transazioni']:
            writer.writerow({
                'numero_progressivo': trans['numero_progressivo'],
                'data_transazione': trans['data_transazione'],
                'data_valuta': trans['data_valuta'],
                'importo': trans['importo'],
                'tipo_movimento': trans['tipo_movimento'],
                'categoria_suggerita': trans['categoria_suggerita'],
                'descrizione': trans['descrizione'],
                'pagina': trans['pagina']
            })
    
    logger.info(f"Esportate {len(data['transazioni'])} transazioni in {output_file}")


def print_summary(data: Dict):
    """Stampa un riepilogo dei dati estratti."""
    print("\n=== RIEPILOGO ESTRATTO CONTO BPER ===\n")
    
    # Info conto
    info = data.get('info_conto', {})
    if info:
        print(f"IBAN: {info.get('iban', 'N/D')}")
        print(f"BIC: {info.get('bic', 'N/D')}")
        print(f"Intestatario: {info.get('intestatario', {}).get('nome', 'N/D')}")
        print(f"Filiale: {info.get('filiale', 'N/D')}")
    
    # Riepilogo
    summary = data.get('riepilogo', {})
    if summary:
        print(f"\nSaldo iniziale: €{summary.get('saldo_iniziale', {}).get('importo', 0):.2f}")
        print(f"Saldo finale: €{summary.get('saldo_finale', {}).get('importo', 0):.2f}")
        print(f"Variazione: €{summary.get('variazione', 0):.2f}")
        print(f"Totale entrate: €{summary.get('totale_entrate', 0):.2f}")
        print(f"Totale uscite: €{summary.get('totale_uscite', 0):.2f}")
    
    # Statistiche
    stats = data.get('statistiche', {})
    if stats:
        print(f"\n=== STATISTICHE ===")
        print(f"Numero transazioni: {stats.get('numero_transazioni', 0)}")
        print(f"- Entrate: {stats.get('numero_entrate', 0)} (media: €{stats.get('media_entrate', 0):.2f})")
        print(f"- Uscite: {stats.get('numero_uscite', 0)} (media: €{stats.get('media_uscite', 0):.2f})")
        
        print(f"\n=== SPESE PER CATEGORIA ===")
        categorie = stats.get('categorie', {})
        for cat, info in sorted(categorie.items(), key=lambda x: x[1]['totale']):
            if info['totale'] < 0:  # Solo spese
                print(f"{cat}: €{abs(info['totale']):.2f} ({info['numero']} transazioni)")


# Esempio di utilizzo
if __name__ == '__main__':
    parser = BPERParser()
    
    # Parse del PDF
    result = parser.parse('estratto_conto_bper.pdf')
    
    # Stampa riepilogo
    print_summary(result)
    
    # Esporta in CSV
    export_to_csv(result)
    
    # Mostra prime 5 transazioni
    print("\n=== PRIME 5 TRANSAZIONI ===")
    for trans in result['transazioni'][:5]:
        print(f"{trans['data_transazione']} | €{trans['importo']:>10.2f} | {trans['categoria_suggerita']:15} | {trans['descrizione'][:50]}...")