# ... gestione_proprieta e funzioni correlate qui ...

from src.repositories.proprieta_repository import ProprietaRepository
from src.repositories.categoria_repository import CategoriaRepository
from src.models.proprieta import Proprieta, TipoProprieta
from src.cli.utils import print_colored
from datetime import datetime

def seleziona_tipo_proprieta():
    tipi = list(TipoProprieta)
    print("\nTipi di proprietà disponibili:")
    for idx, tipo in enumerate(tipi, 1):
        print(f"{idx}. {tipo.value}")
    while True:
        scelta = input("Seleziona il tipo di proprietà (numero): ").strip()
        try:
            idx = int(scelta)
            if 1 <= idx <= len(tipi):
                return tipi[idx - 1]
        except ValueError:
            pass
        print("Scelta non valida. Riprova.")

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

def gestione_proprieta():
    repo = ProprietaRepository()
    cat_repo = CategoriaRepository()
    while True:
        print_colored("\n--- Gestione Proprietà ---", "magenta", bold=True)
        print("1. Visualizza tutte le proprietà")
        print("2. Aggiungi nuova proprietà")
        print("3. Modifica proprietà esistente")
        print("4. Elimina proprietà (con cautela!)")
        print("5. Visualizza proprietà per tipo")
        print("0. Torna al menu principale")
        scelta = input("\nSeleziona un'opzione: ").strip()
        if scelta == "1":
            proprieta = repo.get_all(order_by="id_proprieta")
            if not proprieta:
                print("\nNessuna proprietà presente.")
            else:
                print("\nElenco proprietà:")
                for p in proprieta:
                    data_str = p.data_acquisizione_o_inizio_contratto_affitto.strftime("%Y-%m-%d") if p.data_acquisizione_o_inizio_contratto_affitto else "-"
                    print(f"ID: {p.id_proprieta}, Nome: {p.nome_o_indirizzo_breve}, Tipo: {p.tipo.value}, Data: {data_str}, Valore: {p.valore_acquisto_o_stima_attuale}, Canone Attivo: {p.canone_affitto_mensile_attivo}, Canone Passivo: {p.canone_affitto_mensile_passivo}")
            input("\nPremi Invio per continuare...")
        elif scelta == "2":
            print("\n--- Aggiungi Nuova Proprietà ---")
            nome = input("Nome o indirizzo breve: ").strip()
            tipo = seleziona_tipo_proprieta()
            data_acq = input_data("Data acquisizione o inizio contratto affitto")
            valore = None
            canone_attivo = None
            canone_passivo = None
            if tipo in [TipoProprieta.POSSESSO_USO_PERSONALE, TipoProprieta.POSSESSO_AFFITTATA]:
                valore = input_float("Valore acquisto o stima attuale", obbligatorio=True)
            if tipo == TipoProprieta.POSSESSO_AFFITTATA:
                canone_attivo = input_float("Canone affitto mensile attivo", obbligatorio=True)
            if tipo == TipoProprieta.AFFITTO_PASSIVO:
                canone_passivo = input_float("Canone affitto mensile passivo", obbligatorio=True)
            note = input("Eventuali note legali o scadenze contrattuali (opzionale): ").strip() or None
            try:
                prop = Proprieta(
                    nome_o_indirizzo_breve=nome,
                    tipo=tipo,
                    data_acquisizione_o_inizio_contratto_affitto=data_acq,
                    valore_acquisto_o_stima_attuale=valore,
                    canone_affitto_mensile_attivo=canone_attivo,
                    canone_affitto_mensile_passivo=canone_passivo,
                    eventuali_note_legali_o_scadenze_contrattuali=note
                )
                prop_creata = repo.create(prop)
                print_colored(f"\nProprietà creata con successo! ID: {prop_creata.id_proprieta}", "green")
                # Categorie automatiche
                cat_repo.crea_categorie_per_nuova_proprieta(nome, tipo.value)
                print("Categorie standard per la proprietà create automaticamente.")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "3":
            print("\n--- Modifica Proprietà ---")
            try:
                id_prop = int(input("ID proprietà da modificare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            prop = repo.get_by_id(id_prop)
            if not prop:
                print("Proprietà non trovata.")
                continue
            print(f"Dati attuali - Nome: {prop.nome_o_indirizzo_breve}, Tipo: {prop.tipo.value}")
            nuovo_nome = input("Nuovo nome/indirizzo (Invio per lasciare invariato): ").strip()
            print(f"Tipo attuale: {prop.tipo.value}")
            cambia_tipo = input("Vuoi cambiare il tipo di proprietà? (s/N): ").strip().lower()
            nuovo_tipo = prop.tipo
            if cambia_tipo == "s":
                nuovo_tipo = seleziona_tipo_proprieta()
            nuova_data = input_data("Nuova data acquisizione/inizio contratto (Invio per lasciare invariato)") or prop.data_acquisizione_o_inizio_contratto_affitto
            nuovo_valore = prop.valore_acquisto_o_stima_attuale
            nuovo_canone_attivo = prop.canone_affitto_mensile_attivo
            nuovo_canone_passivo = prop.canone_affitto_mensile_passivo
            if nuovo_tipo in [TipoProprieta.POSSESSO_USO_PERSONALE, TipoProprieta.POSSESSO_AFFITTATA]:
                val = input_float("Nuovo valore acquisto/stima (Invio per lasciare invariato)")
                if val is not None:
                    nuovo_valore = val
            else:
                nuovo_valore = None
            if nuovo_tipo == TipoProprieta.POSSESSO_AFFITTATA:
                val = input_float("Nuovo canone affitto mensile attivo (Invio per lasciare invariato)")
                if val is not None:
                    nuovo_canone_attivo = val
            else:
                nuovo_canone_attivo = None
            if nuovo_tipo == TipoProprieta.AFFITTO_PASSIVO:
                val = input_float("Nuovo canone affitto mensile passivo (Invio per lasciare invariato)")
                if val is not None:
                    nuovo_canone_passivo = val
            else:
                nuovo_canone_passivo = None
            nuova_note = input("Nuove note legali/scadenze (Invio per lasciare invariato): ").strip() or prop.eventuali_note_legali_o_scadenze_contrattuali
            if nuovo_nome:
                prop.nome_o_indirizzo_breve = nuovo_nome
            prop.tipo = nuovo_tipo
            prop.data_acquisizione_o_inizio_contratto_affitto = nuova_data
            prop.valore_acquisto_o_stima_attuale = nuovo_valore
            prop.canone_affitto_mensile_attivo = nuovo_canone_attivo
            prop.canone_affitto_mensile_passivo = nuovo_canone_passivo
            prop.eventuali_note_legali_o_scadenze_contrattuali = nuova_note
            try:
                prop_aggiornata = repo.update(prop)
                print_colored(f"\nProprietà aggiornata con successo! ID: {prop_aggiornata.id_proprieta}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "4":
            print("\n--- Elimina Proprietà ---")
            try:
                id_prop = int(input("ID proprietà da eliminare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            try:
                prop = repo.get_by_id(id_prop)
                if not prop:
                    print("Proprietà non trovata.")
                    continue
                try:
                    repo.delete(id_prop)
                except Exception as e:
                    print_colored(f"\nErrore: {e}", "red")
                    input("\nPremi Invio per continuare...")
                    continue
                conferma = input("Sei sicuro di voler eliminare questa proprietà? Questa azione è irreversibile. (s/N): ").strip().lower()
                if conferma != "s":
                    print("Operazione annullata.")
                    continue
                if repo.delete(id_prop):
                    print_colored("Proprietà eliminata con successo.", "green")
                else:
                    print("Proprietà non trovata.")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "5":
            tipo = seleziona_tipo_proprieta()
            proprieta = repo.get_by_tipo(tipo)
            if not proprieta:
                print(f"\nNessuna proprietà trovata per tipo '{tipo.value}'.")
            else:
                print(f"\nProprietà di tipo '{tipo.value}':")
                for p in proprieta:
                    data_str = p.data_acquisizione_o_inizio_contratto_affitto.strftime("%Y-%m-%d") if p.data_acquisizione_o_inizio_contratto_affitto else "-"
                    print(f"ID: {p.id_proprieta}, Nome: {p.nome_o_indirizzo_breve}, Data: {data_str}, Valore: {p.valore_acquisto_o_stima_attuale}, Canone Attivo: {p.canone_affitto_mensile_attivo}, Canone Passivo: {p.canone_affitto_mensile_passivo}")
            input("\nPremi Invio per continuare...")
        elif scelta == "0":
            break
        else:
            print_colored("\nOpzione non valida. Riprova.", "red")
