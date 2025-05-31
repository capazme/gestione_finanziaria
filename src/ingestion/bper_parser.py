import pdfplumber
import re
from datetime import datetime, date

def parse_bper_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text_pages = [page.extract_text() for page in pdf.pages]

    # 1. Estrai info generali dalla prima pagina
    info_conto = extract_account_info(text_pages[0])

    # 2. Estrai transazioni da tutte le pagine
    transazioni = []
    for page_text in text_pages:
        transazioni += extract_transactions_from_page(page_text)

    return {
        "info_conto": info_conto,
        "transazioni": transazioni
    }

def extract_account_info(page_text):
    # Esempio: cerca IBAN, saldo iniziale/finale e relative date
    iban = re.search(r'IBAN\\s*([A-Z0-9 ]+)', page_text)
    saldo_iniziale = re.search(r'SALDO INIZIALE AL\\s*(\\d{2}/\\d{2}/\\d{2})\\s*([\\d.,]+)', page_text)
    saldo_finale = re.search(r'SALDO FINALE AL\\s*(\\d{2}/\\d{2}/\\d{2})\\s*([\\d.,]+)', page_text)
    return {
        "iban": iban.group(1).replace(' ', '') if iban else None,
        "saldo_iniziale": float(saldo_iniziale.group(2).replace('.', '').replace(',', '.')) if saldo_iniziale else None,
        "data_saldo_iniziale": parse_date(saldo_iniziale.group(1)) if saldo_iniziale else None,
        "saldo_finale": float(saldo_finale.group(2).replace('.', '').replace(',', '.')) if saldo_finale else None,
        "data_saldo_finale": parse_date(saldo_finale.group(1)) if saldo_finale else None,
    }

def extract_transactions_from_page(page_text):
    lines = page_text.splitlines()
    trans_rows = []
    in_movimenti = False
    for line in lines:
        # Identifica inizio tabella movimenti
        if re.match(r'\\s*DATA\\s+VALUTA\\s+USCITE\\s+ENTRATE\\s+DESCRIZIONE', line):
            in_movimenti = True
            continue
        if not in_movimenti:
            continue
        # Filtro righe vuote o piè di pagina
        if not line.strip() or re.match(r'\\s*Pagina \\d+', line):
            continue
        # Riconosci riga di transazione (inizia con data e valuta)
        if re.match(r'\\d{2}/\\d{2}/\\d{2}\\s+\\d{2}/\\d{2}/\\d{2}', line):
            trans_rows.append(line)
        # Gestione descrizioni multilinea: se la riga non inizia con data, è una continuazione della descrizione
        elif trans_rows and not re.match(r'\\d{2}/\\d{2}/\\d{2}\\s+\\d{2}/\\d{2}/\\d{2}', line):
            trans_rows[-1] += ' ' + line.strip()
    # Parsing dettagliato delle righe transazione
    return [parse_transaction_row(row) for row in trans_rows]

def parse_transaction_row(row):
    # Esempio: '01/02/25 01/02/25  123,45        Bonifico da Mario Rossi'
    # Regex robusta per DATA VALUTA USCITE ENTRATE DESCRIZIONE
    pattern = (r'(?P<data>\\d{2}/\\d{2}/\\d{2})\\s+'
               r'(?P<valuta>\\d{2}/\\d{2}/\\d{2})\\s+'
               r'(?P<uscite>[\\d.,]*)\\s*'
               r'(?P<entrate>[\\d.,]*)\\s*'
               r'(?P<descrizione>.+)')
    m = re.match(pattern, row)
    if not m:
        return None
    data_trans = parse_date(m.group('data'))
    data_valuta = parse_date(m.group('valuta'))
    importo_uscita = parse_importo(m.group('uscite'))
    importo_entrata = parse_importo(m.group('entrate'))
    # L'importo finale: positivo per entrata, negativo per uscita
    if importo_entrata is not None:
        importo = importo_entrata
    elif importo_uscita is not None:
        importo = -importo_uscita
    else:
        importo = 0.0
    return {
        'data_transazione': data_trans,
        'data_valuta': data_valuta,
        'descrizione': m.group('descrizione').strip(),
        'importo': importo
    }

def parse_date(s):
    try:
        return datetime.strptime(s, '%d/%m/%y').date()
    except Exception:
        return None

def parse_importo(s):
    if not s or not s.strip():
        return None
    return float(s.replace('.', '').replace(',', '.'))

# Esempio di utilizzo:
if __name__ == '__main__':
    result = parse_bper_pdf('data/Estratto_Conto_corrente_31_03_2025.pdf')
    from pprint import pprint
    pprint(result['info_conto'])
    pprint(result['transazioni'][:5])  # Mostra le prime 5 transazioni
