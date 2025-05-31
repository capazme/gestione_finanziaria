# ... gestione_categorie e funzioni correlate qui ...

from src.repositories.categoria_repository import CategoriaRepository
from src.models.categoria_transazione import CategoriaTransazione
from src.cli.utils import print_colored

def gestione_categorie():
    repo = CategoriaRepository()
    while True:
        print_colored("\n--- Gestione Categorie ---", "yellow", bold=True)
        print("1. Visualizza tutte le categorie")
        print("2. Aggiungi nuova categoria")
        print("3. Modifica categoria esistente")
        print("4. Elimina categoria")
        print("5. Visualizza categorie per tipo macro")
        print("6. Visualizza categorie per una proprietà specifica")
        print("0. Torna al menu principale")
        scelta = input("\nSeleziona un'opzione: ").strip()
        if scelta == "1":
            categorie = repo.get_all(order_by="id_categoria")
            if not categorie:
                print("\nNessuna categoria presente.")
            else:
                print("\nElenco categorie:")
                for cat in categorie:
                    print(f"ID: {cat.id_categoria}, Nome: {cat.nome_categoria}, Tipo Macro: {cat.tipo_macro}")
            input("\nPremi Invio per continuare...")
        elif scelta == "2":
            print("\n--- Aggiungi Nuova Categoria ---")
            nome = input("Nome categoria: ").strip()
            tipo_macro = input("Tipo macro (es. Personale, Immobile Casa Rossi): ").strip()
            try:
                categoria = CategoriaTransazione(nome_categoria=nome, tipo_macro=tipo_macro)
                cat_creata = repo.create(categoria)
                print_colored(f"\nCategoria creata con successo! ID: {cat_creata.id_categoria}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "3":
            print("\n--- Modifica Categoria ---")
            try:
                id_cat = int(input("ID categoria da modificare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            cat = repo.get_by_id(id_cat)
            if not cat:
                print("Categoria non trovata.")
                continue
            print(f"Dati attuali - Nome: {cat.nome_categoria}, Tipo Macro: {cat.tipo_macro}")
            nuovo_nome = input("Nuovo nome categoria (Invio per lasciare invariato): ").strip()
            nuovo_tipo = input("Nuovo tipo macro (Invio per lasciare invariato): ").strip()
            if nuovo_nome:
                cat.nome_categoria = nuovo_nome
            if nuovo_tipo:
                cat.tipo_macro = nuovo_tipo
            try:
                cat_aggiornata = repo.update(cat)
                print_colored(f"\nCategoria aggiornata con successo! ID: {cat_aggiornata.id_categoria}", "green")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "4":
            print("\n--- Elimina Categoria ---")
            try:
                id_cat = int(input("ID categoria da eliminare: ").strip())
            except ValueError:
                print("ID non valido.")
                continue
            try:
                if repo.delete(id_cat):
                    print_colored("Categoria eliminata con successo.", "green")
                else:
                    print("Categoria non trovata.")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "5":
            tipo_macro = input("Tipo macro da cercare (es. Personale): ").strip()
            categorie = repo.get_by_tipo_macro(tipo_macro)
            if not categorie:
                print("\nNessuna categoria trovata per questo tipo macro.")
            else:
                print(f"\nCategorie per tipo macro '{tipo_macro}':")
                for cat in categorie:
                    print(f"ID: {cat.id_categoria}, Nome: {cat.nome_categoria}, Tipo Macro: {cat.tipo_macro}")
            input("\nPremi Invio per continuare...")
        elif scelta == "6":
            nome_prop = input("Nome della proprietà (es. Casa Via Rossi): ").strip()
            categorie = repo.get_categorie_per_proprieta(nome_prop)
            if not categorie:
                print("\nNessuna categoria trovata per questa proprietà.")
            else:
                print(f"\nCategorie per proprietà '{nome_prop}':")
                for cat in categorie:
                    print(f"ID: {cat.id_categoria}, Nome: {cat.nome_categoria}, Tipo Macro: {cat.tipo_macro}")
            input("\nPremi Invio per continuare...")
        elif scelta == "0":
            break
        else:
            print_colored("\nOpzione non valida. Riprova.", "red")
