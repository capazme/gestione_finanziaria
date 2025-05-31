# ... gestione_import_pdf e funzioni correlate qui ... 

from src.repositories.conto_repository import ContoRepository
from src.repositories.categoria_repository import CategoriaRepository
from src.repositories.proprieta_repository import ProprietaRepository
from src.repositories.transazione_repository import TransazioneRepository
from src.models.transazione import Transazione, TipoFlusso
from src.services.saldo_calculator import SaldoCalculator
from src.ingestion.bper_parser import parse_bper_pdf
from src.cli.utils import print_colored
import os
from datetime import datetime

def seleziona_tipo_flusso():
    tipi = list(TipoFlusso)
    print("\nTipi di flusso disponibili:")
    for idx, tipo in enumerate(tipi, 1):
        print(f"{idx}. {tipo.value}")
    while True:
        scelta = input("Seleziona il tipo di flusso (numero): ").strip()
        try:
            idx = int(scelta)
            if 1 <= idx <= len(tipi):
                return tipi[idx - 1]
        except ValueError:
            pass
        print("Scelta non valida. Riprova.")

def seleziona_da_elenco(elenco, label, attr_nome="nome_categoria", attr_id="id_categoria", obbligatorio=True):
    if not elenco:
        print(f"Nessun elemento disponibile per {label}.")
        return None
    print(f"\nSeleziona {label}:")
    for e in elenco:
        print(f"{getattr(e, attr_id)}. {getattr(e, attr_nome)}")
    while True:
        val = input(f"ID {label}: ").strip()
        if not val and not obbligatorio:
            return None
        try:
            id_val = int(val)
            for e in elenco:
                if getattr(e, attr_id) == id_val:
                    return e
        except ValueError:
            pass
        print("ID non valido. Riprova.")

def gestione_import_pdf():
    print_colored("\n--- Importa Estratto Conto PDF ---", "cyan", bold=True)
    percorso_pdf = input("Percorso file PDF da importare: ").strip()
    if not os.path.isfile(percorso_pdf):
        print_colored("File non trovato.", "red")
        input("\nPremi Invio per continuare...")
        return
    conto_repo = ContoRepository()
    conti = conto_repo.get_all(order_by="id_conto")
    if not conti:
        print_colored("Nessun conto disponibile. Crea prima un conto.", "yellow")
        input("\nPremi Invio per continuare...")
        return
    print("\nConti disponibili:")
    for c in conti:
        print(f"{c.id_conto}. {c.nome_conto} (Saldo attuale: €{c.saldo_attuale:.2f})")
    try:
        id_conto = int(input("ID conto a cui associare le transazioni: ").strip())
    except ValueError:
        print_colored("ID non valido.", "red")
        input("\nPremi Invio per continuare...")
        return
    conto = conto_repo.get_by_id(id_conto)
    if not conto:
        print_colored("Conto non trovato.", "red")
        input("\nPremi Invio per continuare...")
        return
    print("Parsing PDF in corso...")
    try:
        parsed = parse_bper_pdf(percorso_pdf)
    except Exception as e:
        print_colored(f"Errore durante il parsing del PDF: {e}", "red")
        input("\nPremi Invio per continuare...")
        return
    info_conto = parsed['info_conto']
    trans_estratte = parsed['transazioni']
    print("\nInfo estratte dal PDF:")
    for k, v in info_conto.items():
        print(f"  {k}: {v}")
    if info_conto['saldo_iniziale'] is not None and abs(conto.saldo_attuale - info_conto['saldo_iniziale']) > 0.01:
        print_colored(f"\nATTENZIONE: Il saldo attuale del conto (€{conto.saldo_attuale:.2f}) è diverso dal saldo iniziale dell'estratto conto (€{info_conto['saldo_iniziale']:.2f})!", "yellow")
        print("Potrebbero mancare transazioni precedenti o l'estratto conto non è il successivo logico.")
    cat_repo = CategoriaRepository()
    prop_repo = ProprietaRepository()
    trans_repo = TransazioneRepository()
    saldo_calc = SaldoCalculator()
    importate = 0
    for idx, t in enumerate(trans_estratte, 1):
        print(f"\n--- Revisione transazione {idx}/{len(trans_estratte)} ---")
        print(f"Data: {t['data_transazione']}, Valuta: {t['data_valuta']}, Importo: {t['importo']}, Desc: {t['descrizione']}")
        data = input(f"Data transazione (Invio per {t['data_transazione']}): ").strip() or t['data_transazione']
        try:
            if isinstance(data, str):
                data = datetime.strptime(data, '%Y-%m-%d').date()
        except Exception:
            print_colored("Data non valida. Salto transazione.", "red")
            continue
        importo = input(f"Importo (Invio per {t['importo']}): ").strip()
        importo = float(importo) if importo else t['importo']
        descrizione = input(f"Descrizione (Invio per '{t['descrizione']}'): ").strip() or t['descrizione']
        categorie = cat_repo.get_all(order_by="id_categoria")
        cat = seleziona_da_elenco(categorie, "categoria")
        prop = None
        if input("Associare una proprietà? (s/N): ").strip().lower() == "s":
            props = prop_repo.get_all(order_by="id_proprieta")
            prop = seleziona_da_elenco(props, "proprietà", attr_nome="nome_o_indirizzo_breve", attr_id="id_proprieta", obbligatorio=False)
        tipo_flusso = seleziona_tipo_flusso()
        flag_fiscale = input("Rilevante fiscalmente/deducibile? (s/N): ").strip().lower() == "s"
        note = input("Note aggiuntive (opzionale): ").strip() or None
        azione = input("Salva questa transazione? (s = salva, n = salta, x = interrompi importazione): ").strip().lower()
        if azione == "x":
            print_colored("Importazione interrotta dall'utente.", "yellow")
            break
        if azione != "s":
            print("Transazione saltata.")
            continue
        try:
            trans = Transazione(
                data=data,
                importo=importo,
                descrizione=descrizione,
                id_categoria=cat.id_categoria,
                id_conto_finanziario=conto.id_conto,
                id_proprieta_associata=prop.id_proprieta if prop else None,
                tipo_flusso=tipo_flusso,
                flag_deducibile_o_rilevante_fiscalmente=flag_fiscale,
                note_aggiuntive=note
            )
            trans_creata = trans_repo.create(trans)
            saldo_calc.aggiorna_saldo_dopo_modifica_transazione(trans_creata, 'create')
            importate += 1
            print_colored("Transazione importata con successo.", "green")
        except Exception as e:
            print_colored(f"Errore durante il salvataggio: {e}", "red")
    print_colored(f"\nImportazione completata. {importate} transazioni importate.", "cyan")
    conto_aggiornato = conto_repo.get_by_id(conto.id_conto)
    if info_conto['saldo_finale'] is not None:
        if abs(conto_aggiornato.saldo_attuale - info_conto['saldo_finale']) < 0.01:
            print_colored(f"Saldo finale del conto (€{conto_aggiornato.saldo_attuale:.2f}) coincide con quello dell'estratto conto.", "green")
        else:
            print_colored(f"ATTENZIONE: Saldo finale del conto (€{conto_aggiornato.saldo_attuale:.2f}) DIVERSO da quello dell'estratto conto (€{info_conto['saldo_finale']:.2f})!", "red")
    input("\nPremi Invio per tornare al menu principale...") 