import sys
from src.cli.utils import print_logo, print_colored, show_tutorial, check_first_setup
from src.cli.commands.categoria_commands import gestione_categorie
from src.cli.commands.conto_commands import gestione_conti
from src.cli.commands.proprieta_commands import gestione_proprieta
from src.cli.commands.transazione_commands import gestione_transazioni
from src.cli.commands.report_commands import visualizza_report
from src.cli.commands.ingestion_commands import gestione_import_pdf
import os
from pathlib import Path

def setup_iniziale():
    """
    Inizializza il database e applica le migrazioni se necessario.
    """
    from src.database.database_connection import init_database
    from src.database.migrations import migrate_to_latest
    db_path = Path(__file__).parent.parent.parent / "data" / "database.db"
    if not db_path.exists() or os.path.getsize(db_path) < 1024:  # file non esiste o troppo piccolo
        print_colored("\n[Setup] Inizializzazione database in corso...", "yellow", bold=True)
        try:
            init_database()
            migrate_to_latest()
            print_colored("Database creato e aggiornato con successo!", "green")
        except Exception as e:
            print_colored(f"Errore durante l'inizializzazione del database: {e}", "red")
            sys.exit(1)
    else:
        try:
            migrate_to_latest()
        except Exception as e:
            print_colored(f"Errore durante le migrazioni: {e}", "red")
            sys.exit(1)

def menu_principale():
    print_logo()
    setup_iniziale()
    if check_first_setup():
        show_tutorial()
    while True:
        print_colored("\n=== Sistema Gestione Finanziaria ===", "cyan", bold=True)
        print("1. Gestione Proprietà")
        print("2. Gestione Conti")
        print("3. Gestione Categorie")
        print("4. Gestione Transazioni")
        print("5. Visualizza Report")
        print("6. Importa Estratto Conto PDF")
        print("7. Tutorial/Guida Rapida")
        print("0. Esci")
        scelta = input("\nSeleziona un'opzione: ").strip()
        if scelta == "1":
            gestione_proprieta()
        elif scelta == "2":
            gestione_conti()
        elif scelta == "3":
            gestione_categorie()
        elif scelta == "4":
            gestione_transazioni()
        elif scelta == "5":
            visualizza_report()
        elif scelta == "6":
            gestione_import_pdf()
        elif scelta == "7":
            show_tutorial()
        elif scelta == "0":
            print_colored("\nArrivederci!", "green", bold=True)
            sys.exit(0)
        else:
            print_colored("\nOpzione non valida. Riprova.", "red")

if __name__ == "__main__":
    menu_principale()
