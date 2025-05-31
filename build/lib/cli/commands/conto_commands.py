# ... gestione_conti e funzioni correlate qui ...

from src.repositories.conto_repository import ContoRepository
from src.repositories.transazione_repository import TransazioneRepository
from src.services.saldo_calculator import SaldoCalculator
from src.models.conto_finanziario import ContoFinanziario, TipoConto
from src.cli.utils import print_colored

def seleziona_tipo_conto():
    tipi = list(TipoConto)
    print("\nTipi di conto disponibili:")
    for idx, tipo in enumerate(tipi, 1):
        print(f"{idx}. {tipo.value}")
    while True:
        scelta = input("Seleziona il tipo di conto (numero): ").strip()
        try:
            idx = int(scelta)
            if 1 <= idx <= len(tipi):
                return tipi[idx - 1]
        except ValueError:
            pass
        print("Scelta non valida. Riprova.")

def gestione_conti():
    repo = ContoRepository()
    trans_repo = TransazioneRepository()
    saldo_calc = SaldoCalculator()
    while True:
        print_colored("\n--- Gestione Conti Finanziari ---", "blue", bold=True)
        print("1. Visualizza tutti i conti")
        print("2. Aggiungi nuovo conto")
        print("3. Modifica conto esistente")
        print("4. Elimina conto (con cautela!)")
        print("5. Visualizza conti per tipo")
        print("6. Ricalcola saldo di un conto")
        print("7. Verifica coerenza saldi di tutti i conti")
        print("0. Torna al menu principale")
        scelta = input("\nSeleziona un'opzione: ").strip()
        if scelta == "1":
            conti = repo.get_all(order_by="id_conto")
            if not conti:
                print("\nNessun conto presente.")
            else:
                print("\nElenco conti:")
                for c in conti:
                    print(f"ID: {c.id_conto}, Nome: {c.nome_conto}, Tipo: {c.tipo_conto.value}, Saldo Iniziale: €{c.saldo_iniziale:.2f}, Saldo Attuale: €{c.saldo_attuale:.2f}")
            input("\nPremi Invio per continuare...")
        elif scelta == "2":
            print("\n--- Aggiungi Nuovo Conto ---")
            nome = input("Nome conto: ").strip()
            while True:
                saldo_iniziale_str = input("Saldo iniziale: ").strip()
                try:
                    saldo_iniziale = float(saldo_iniziale_str)
                    break
                except ValueError:
                    print("Valore non valido. Inserisci un numero.")
            tipo_conto = seleziona_tipo_conto()
            try:
                conto = ContoFinanziario(nome_conto=nome, saldo_iniziale=saldo_iniziale, tipo_conto=tipo_conto, saldo_attuale=saldo_iniziale)
                conto_creato = repo.create(conto)
                print_colored(f"\nConto creato con successo! ID: {conto_creato.id_conto}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "3":
            print("\n--- Modifica Conto ---")
            try:
                id_conto = int(input("ID conto da modificare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            conto = repo.get_by_id(id_conto)
            if not conto:
                print("Conto non trovato.")
                continue
            print(f"Dati attuali - Nome: {conto.nome_conto}, Saldo Iniziale: €{conto.saldo_iniziale:.2f}, Tipo: {conto.tipo_conto.value}")
            nuovo_nome = input("Nuovo nome conto (Invio per lasciare invariato): ").strip()
            nuovo_saldo_str = input("Nuovo saldo iniziale (Invio per lasciare invariato): ").strip()
            print("Tipo conto attuale:", conto.tipo_conto.value)
            cambia_tipo = input("Vuoi cambiare il tipo di conto? (s/N): ").strip().lower()
            if nuovo_nome:
                conto.nome_conto = nuovo_nome
            if nuovo_saldo_str:
                try:
                    nuovo_saldo = float(nuovo_saldo_str)
                    conto.saldo_iniziale = nuovo_saldo
                    print_colored("Attenzione: hai modificato il saldo iniziale. Potrebbe essere necessario ricalcolare il saldo attuale tramite l'opzione 6.", "yellow")
                except ValueError:
                    print_colored("Valore saldo non valido. Modifica ignorata.", "red")
            if cambia_tipo == "s":
                conto.tipo_conto = seleziona_tipo_conto()
            try:
                conto_aggiornato = repo.update(conto)
                print_colored(f"\nConto aggiornato con successo! ID: {conto_aggiornato.id_conto}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "4":
            print("\n--- Elimina Conto ---")
            try:
                id_conto = int(input("ID conto da eliminare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            transazioni = trans_repo.get_by_conto_id(id_conto)
            if transazioni:
                print_colored("Impossibile eliminare: il conto ha transazioni associate. Considera di spostare le transazioni o archiviare il conto.", "yellow")
                input("\nPremi Invio per continuare...")
                continue
            conferma = input("Sei sicuro di voler eliminare questo conto? Questa azione è irreversibile. (s/N): ").strip().lower()
            if conferma != "s":
                print("Operazione annullata.")
                continue
            try:
                if repo.delete(id_conto):
                    print_colored("Conto eliminato con successo.", "green")
                else:
                    print("Conto non trovato.")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "5":
            tipo_conto = seleziona_tipo_conto()
            conti = repo.get_by_tipo(tipo_conto.value)
            if not conti:
                print(f"\nNessun conto trovato per tipo '{tipo_conto.value}'.")
            else:
                print(f"\nConti di tipo '{tipo_conto.value}':")
                for c in conti:
                    print(f"ID: {c.id_conto}, Nome: {c.nome_conto}, Saldo Iniziale: €{c.saldo_iniziale:.2f}, Saldo Attuale: €{c.saldo_attuale:.2f}")
            input("\nPremi Invio per continuare...")
        elif scelta == "6":
            print("\n--- Ricalcola Saldo Conto ---")
            try:
                id_conto = int(input("ID conto per ricalcolo saldo: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            try:
                conto_aggiornato = saldo_calc.ricalcola_e_aggiorna_saldo_conto(id_conto)
                print_colored(f"Saldo aggiornato: €{conto_aggiornato.saldo_attuale:.2f}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "7":
            print("\n--- Verifica Coerenza Saldi Tutti i Conti ---")
            risultati = saldo_calc.verifica_coerenza_saldi_tutti_conti()
            conti = repo.get_all()
            incoerenti = False
            for c in conti:
                coerente = risultati.get(c.id_conto, True)
                stato = "OK" if coerente else "NON COERENTE"
                print(f"ID: {c.id_conto}, Nome: {c.nome_conto}, Saldo Attuale: €{c.saldo_attuale:.2f} [{stato}]")
                if not coerente:
                    incoerenti = True
            if not incoerenti:
                print_colored("\nTutti i saldi sono coerenti.", "green")
            input("\nPremi Invio per continuare...")
        elif scelta == "0":
            break
        else:
            print_colored("\nOpzione non valida. Riprova.", "red")
