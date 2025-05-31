def print_logo():
    logo = r'''
  ____           _   _ _       _             _ _             
 / ___| ___  ___| |_(_) |_ ___| |_ _ __ __ _| (_)_ __   __ _ 
| |  _ / _ \/ __| __| | __/ __| __| '__/ _` | | | '_ \ / _` |
| |_| |  __/\__ \ |_| | |_\__ \ |_| | | (_| | | | | | | (_| |
 \____|\___||___/\__|_|\__|___/\__|_|  \__,_|_|_|_| |_|\__, |
                                                      |___/ 
'''
    print_colored(logo, "green", bold=True)

def print_colored(text, color=None, bold=False):
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        color_map = {
            "red": Fore.RED,
            "green": Fore.GREEN,
            "yellow": Fore.YELLOW,
            "blue": Fore.BLUE,
            "magenta": Fore.MAGENTA,
            "cyan": Fore.CYAN,
            "white": Fore.WHITE,
        }
        c = color_map.get(color, "")
        b = Style.BRIGHT if bold else ""
        print(f"{b}{c}{text}{Style.RESET_ALL}")
    except ImportError:
        print(text)

def show_tutorial():
    print_colored("\n=== Benvenuto nel Sistema Gestione Finanziaria! ===", "cyan", bold=True)
    print("\nQuesta applicazione ti permette di:")
    print("- Gestire proprietà, conti, categorie e transazioni")
    print("- Importare estratti conto PDF e categorizzare le operazioni")
    print("- Visualizzare report di cash flow, P&L immobili, riepiloghi fiscali e patrimonio netto")
    print("\nPrimi passi consigliati:")
    print("1. Aggiungi almeno un conto finanziario (Gestione Conti)")
    print("2. Aggiungi le categorie di spesa/entrata che usi più spesso (Gestione Categorie)")
    print("3. Inserisci le tue proprietà immobiliari (Gestione Proprietà)")
    print("4. Inserisci o importa le prime transazioni (Gestione Transazioni o Importa PDF)")
    print("5. Esplora i report per monitorare la tua situazione finanziaria")
    print("\nPer assistenza, puoi richiamare questa guida dal menu principale.")
    input("\nPremi Invio per continuare...")

def check_first_setup():
    try:
        from src.repositories.conto_repository import ContoRepository
        from src.repositories.proprieta_repository import ProprietaRepository
        from src.repositories.categoria_repository import CategoriaRepository
        from src.repositories.transazione_repository import TransazioneRepository
        if not ContoRepository().get_all() or not CategoriaRepository().get_all() or not ProprietaRepository().get_all():
            return True
        return False
    except Exception:
        return False
