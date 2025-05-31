# ... gestione_transazioni e funzioni correlate qui ...

from src.repositories.transazione_repository import TransazioneRepository
from src.repositories.categoria_repository import CategoriaRepository
from src.repositories.conto_repository import ContoRepository
from src.repositories.proprieta_repository import ProprietaRepository
from src.services.saldo_calculator import SaldoCalculator
from src.models.transazione import Transazione, TipoFlusso
from src.cli.utils import print_colored
from datetime import datetime, date, timedelta

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

def stampa_transazione(t, cat_repo, conto_repo, prop_repo):
    cat = cat_repo.get_by_id(t.id_categoria)
    conto = conto_repo.get_by_id(t.id_conto_finanziario)
    prop = prop_repo.get_by_id(t.id_proprieta_associata) if t.id_proprieta_associata else None
    data_str = t.data.strftime("%Y-%m-%d")
    importo_str = f"+€{t.importo:.2f}" if t.importo > 0 else f"-€{abs(t.importo):.2f}"
    print(f"ID: {t.id_transazione}, Data: {data_str}, Importo: {importo_str}, Desc: {t.descrizione}, Categoria: {cat.nome_categoria if cat else t.id_categoria}, Conto: {conto.nome_conto if conto else t.id_conto_finanziario}, Proprietà: {prop.nome_o_indirizzo_breve if prop else '-'}")

def input_data(label):
    while True:
        val = input(f"{label} (YYYY-MM-DD): ").strip()
        if not val:
            return None
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            print("Formato data non valido. Riprova.")

def input_float(label, obbligatorio=False):
    while True:
        val = input(f"{label}: ").strip()
        if not val and not obbligatorio:
            return None
        try:
            return float(val)
        except ValueError:
            print("Valore non valido. Inserisci un numero.")

def gestione_transazioni():
    repo = TransazioneRepository()
    cat_repo = CategoriaRepository()
    conto_repo = ContoRepository()
    prop_repo = ProprietaRepository()
    saldo_calc = SaldoCalculator()
    while True:
        print_colored("\n--- Gestione Transazioni ---", "cyan", bold=True)
        print("1. Visualizza transazioni recenti")
        print("2. Aggiungi nuova transazione")
        print("3. Modifica transazione esistente")
        print("4. Elimina transazione")
        print("5. Ricerca transazioni")
        print("0. Torna al menu principale")
        scelta = input("\nSeleziona un'opzione: ").strip()
        if scelta == "1":
            print("\n1. Ultime 10 transazioni\n2. Transazioni mese corrente\n3. Transazioni mese precedente")
            sub = input("Scegli criterio (1/2/3): ").strip()
            oggi = date.today()
            if sub == "1":
                trans = repo.get_by_periodo(date(1900,1,1), oggi, order_by="data DESC")[:10]
            elif sub == "2":
                data_inizio = oggi.replace(day=1)
                data_fine = oggi
                trans = repo.get_by_periodo(data_inizio, data_fine, order_by="data DESC")
            elif sub == "3":
                primo_oggi = oggi.replace(day=1)
                mese_prec = primo_oggi - timedelta(days=1)
                data_inizio = mese_prec.replace(day=1)
                data_fine = mese_prec.replace(day=mese_prec.day)
                trans = repo.get_by_periodo(data_inizio, data_fine, order_by="data DESC")
            else:
                print("Criterio non valido.")
                continue
            if not trans:
                print("\nNessuna transazione trovata.")
            else:
                print("\nTransazioni:")
                for t in trans:
                    stampa_transazione(t, cat_repo, conto_repo, prop_repo)
            input("\nPremi Invio per continuare...")
        elif scelta == "2":
            print("\n--- Aggiungi Nuova Transazione ---")
            data = input_data("Data transazione (Invio per oggi)") or datetime.today().date()
            importo = input_float("Importo (positivo per entrata, negativo per uscita)", obbligatorio=True)
            descrizione = input("Descrizione: ").strip()
            categorie = cat_repo.get_all(order_by="id_categoria")
            cat = seleziona_da_elenco(categorie, "categoria")
            conti = conto_repo.get_all(order_by="id_conto")
            conto = seleziona_da_elenco(conti, "conto", attr_nome="nome_conto", attr_id="id_conto")
            prop = None
            if input("Associare una proprietà? (s/N): ").strip().lower() == "s":
                props = prop_repo.get_all(order_by="id_proprieta")
                prop = seleziona_da_elenco(props, "proprietà", attr_nome="nome_o_indirizzo_breve", attr_id="id_proprieta", obbligatorio=False)
            tipo_flusso = seleziona_tipo_flusso()
            flag_fiscale = input("Rilevante fiscalmente/deducibile? (s/N): ").strip().lower() == "s"
            note = input("Note aggiuntive (opzionale): ").strip() or None
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
                trans_creata = repo.create(trans)
                saldo_calc.aggiorna_saldo_dopo_modifica_transazione(trans_creata, 'create')
                print_colored(f"\nTransazione creata con successo! ID: {trans_creata.id_transazione}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "3":
            print("\n--- Modifica Transazione ---")
            try:
                id_tr = int(input("ID transazione da modificare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            trans = repo.get_by_id(id_tr)
            if not trans:
                print("Transazione non trovata.")
                continue
            print("Dati attuali:")
            stampa_transazione(trans, cat_repo, conto_repo, prop_repo)
            data = input_data("Nuova data (Invio per lasciare invariato)") or trans.data
            importo = input_float("Nuovo importo (Invio per lasciare invariato)") or trans.importo
            descrizione = input("Nuova descrizione (Invio per lasciare invariato): ").strip() or trans.descrizione
            categorie = cat_repo.get_all(order_by="id_categoria")
            cat = seleziona_da_elenco(categorie, "categoria") or cat_repo.get_by_id(trans.id_categoria)
            conti = conto_repo.get_all(order_by="id_conto")
            conto = seleziona_da_elenco(conti, "conto", attr_nome="nome_conto", attr_id="id_conto") or conto_repo.get_by_id(trans.id_conto_finanziario)
            prop = None
            if input("Associare una proprietà? (s/N, Invio per lasciare invariato): ").strip().lower() == "s":
                props = prop_repo.get_all(order_by="id_proprieta")
                prop = seleziona_da_elenco(props, "proprietà", attr_nome="nome_o_indirizzo_breve", attr_id="id_proprieta", obbligatorio=False)
            else:
                prop = prop_repo.get_by_id(trans.id_proprieta_associata) if trans.id_proprieta_associata else None
            tipo_flusso = seleziona_tipo_flusso() or trans.tipo_flusso
            flag_fiscale = input("Rilevante fiscalmente/deducibile? (s/N, Invio per lasciare invariato): ").strip().lower()
            if flag_fiscale == "s":
                flag_fiscale = True
            elif flag_fiscale == "n":
                flag_fiscale = False
            else:
                flag_fiscale = trans.flag_deducibile_o_rilevante_fiscalmente
            note = input("Nuove note aggiuntive (Invio per lasciare invariato): ").strip() or trans.note_aggiuntive
            trans_precedente = repo.get_by_id(id_tr)
            conto_orig = trans_precedente.id_conto_finanziario if trans_precedente else None
            try:
                trans.data = data
                trans.importo = importo
                trans.descrizione = descrizione
                trans.id_categoria = cat.id_categoria
                trans.id_conto_finanziario = conto.id_conto
                trans.id_proprieta_associata = prop.id_proprieta if prop else None
                trans.tipo_flusso = tipo_flusso
                trans.flag_deducibile_o_rilevante_fiscalmente = flag_fiscale
                trans.note_aggiuntive = note
                trans_aggiornata = repo.update(trans)
                saldo_calc.aggiorna_saldo_dopo_modifica_transazione(trans_aggiornata, 'update', trans_precedente)
                print_colored(f"\nTransazione aggiornata con successo! ID: {trans_aggiornata.id_transazione}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "4":
            print("\n--- Elimina Transazione ---")
            try:
                id_tr = int(input("ID transazione da eliminare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            trans = repo.get_by_id(id_tr)
            if not trans:
                print("Transazione non trovata.")
                continue
            stampa_transazione(trans, cat_repo, conto_repo, prop_repo)
            conferma = input("Sei sicuro di voler eliminare questa transazione? (s/N): ").strip().lower()
            if conferma != "s":
                print("Operazione annullata.")
                continue
            try:
                if repo.delete(id_tr):
                    saldo_calc.aggiorna_saldo_dopo_modifica_transazione(trans, 'delete')
                    print_colored("Transazione eliminata con successo.", "green")
                else:
                    print("Transazione non trovata.")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "5":
            print("\n--- Ricerca Transazioni ---")
            data_inizio = input_data("Data inizio (Invio per nessun filtro)")
            data_fine = input_data("Data fine (Invio per nessun filtro)")
            categorie = cat_repo.get_all(order_by="id_categoria")
            cat = seleziona_da_elenco(categorie, "categoria", obbligatorio=False)
            conti = conto_repo.get_all(order_by="id_conto")
            conto = seleziona_da_elenco(conti, "conto", attr_nome="nome_conto", attr_id="id_conto", obbligatorio=False)
            props = prop_repo.get_all(order_by="id_proprieta")
            prop = seleziona_da_elenco(props, "proprietà", attr_nome="nome_o_indirizzo_breve", attr_id="id_proprieta", obbligatorio=False)
            tipo_flusso = None
            if input("Filtrare per tipo flusso? (s/N): ").strip().lower() == "s":
                tipo_flusso = seleziona_tipo_flusso()
            solo_fiscale = input("Solo fiscalmente rilevanti? (s/N): ").strip().lower() == "s"
            trans = repo.get_all(order_by="data DESC")
            risultati = []
            for t in trans:
                if data_inizio and t.data < data_inizio:
                    continue
                if data_fine and t.data > data_fine:
                    continue
                if cat and t.id_categoria != cat.id_categoria:
                    continue
                if conto and t.id_conto_finanziario != conto.id_conto:
                    continue
                if prop and t.id_proprieta_associata != prop.id_proprieta:
                    continue
                if tipo_flusso and t.tipo_flusso != tipo_flusso:
                    continue
                if solo_fiscale and not t.flag_deducibile_o_rilevante_fiscalmente:
                    continue
                risultati.append(t)
            if not risultati:
                print("\nNessuna transazione trovata per i filtri selezionati.")
            else:
                print(f"\n{len(risultati)} transazioni trovate:")
                for t in risultati:
                    stampa_transazione(t, cat_repo, conto_repo, prop_repo)
            input("\nPremi Invio per continuare...")
        elif scelta == "0":
            break
        else:
            print_colored("\nOpzione non valida. Riprova.", "red")
