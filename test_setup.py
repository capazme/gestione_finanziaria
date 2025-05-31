"""
# test_setup.py
Script di test per verificare il setup iniziale del sistema.
Crea dati di esempio e testa le funzionalità base.
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.models.models import (
    Proprieta, ContoFinanziario, CategoriaTransazione, Transazione,
    TipoProprieta, TipoConto, TipoFlusso, TipoMacroCategoria
)
from database.connection import init_database, get_database_stats, backup_database


def setup_test_environment():
    """Inizializza l'ambiente di test con dati di esempio."""
    print("=== SETUP SISTEMA GESTIONE FINANZIARIA ===\n")
    
    # 1. Inizializza database
    print("1. Inizializzazione database...")
    try:
        init_database(force_recreate=True)  # Ricrea da zero per test
        print("   ✓ Database creato con successo")
    except Exception as e:
        print(f"   ✗ Errore: {e}")
        return False
    
    # 2. Verifica creazione tabelle
    print("\n2. Verifica struttura database...")
    stats = get_database_stats()
    print(f"   - Proprietà: {stats['proprieta_count']} record")
    print(f"   - Conti: {stats['conto_finanziario_count']} record")
    print(f"   - Categorie: {stats['categoria_transazione_count']} record")
    print(f"   - Transazioni: {stats['transazione_count']} record")
    print(f"   - Dimensione DB: {stats['database_size_mb']:.2f} MB")
    
    # 3. Test creazione modelli
    print("\n3. Test creazione modelli...")
    
    # Test Proprietà
    try:
        casa_proprieta = Proprieta(
            nome_o_indirizzo_breve="Casa Via Roma 123",
            tipo=TipoProprieta.POSSESSO_AFFITTATA,
            data_acquisizione_o_inizio_contratto_affitto=date(2020, 3, 15),
            valore_acquisto_o_stima_attuale=280000,
            canone_affitto_mensile_attivo=1500
        )
        print(f"   ✓ Proprietà creata: {casa_proprieta}")
        print(f"     Rendimento annuo: {casa_proprieta.calcola_rendimento_annuo_lordo():.2f}%")
    except Exception as e:
        print(f"   ✗ Errore creazione proprietà: {e}")
        return False
    
    # Test Conto
    try:
        conto = ContoFinanziario(
            nome_conto="Conto Corrente Intesa",
            saldo_iniziale=10000.0,
            tipo_conto=TipoConto.BANCARIO
        )
        print(f"   ✓ Conto creato: {conto}")
    except Exception as e:
        print(f"   ✗ Errore creazione conto: {e}")
        return False
    
    # Test Categoria
    try:
        categoria = CategoriaTransazione(
            nome_categoria="Stipendio",
            tipo_macro=TipoMacroCategoria.PERSONALE.value
        )
        print(f"   ✓ Categoria creata: {categoria}")
    except Exception as e:
        print(f"   ✗ Errore creazione categoria: {e}")
        return False
    
    # Test Transazione
    try:
        transazione = Transazione(
            data=date.today(),
            importo=2500.0,
            descrizione="Stipendio mensile tirocinio",
            id_categoria=1,  # Assumiamo ID 1 per test
            id_conto_finanziario=1,  # Assumiamo ID 1 per test
            tipo_flusso=TipoFlusso.PERSONALE,
            flag_deducibile_o_rilevante_fiscalmente=True
        )
        print(f"   ✓ Transazione creata: {transazione}")
    except Exception as e:
        print(f"   ✗ Errore creazione transazione: {e}")
        return False
    
    # 4. Test backup
    print("\n4. Test backup database...")
    try:
        backup_file = backup_database()
        print(f"   ✓ Backup creato: {backup_file}")
    except Exception as e:
        print(f"   ✗ Errore backup: {e}")
    
    return True


def test_repository_pattern():
    """Testa il funzionamento dei repository se implementati."""
    print("\n=== TEST REPOSITORY PATTERN ===\n")
    
    try:
        from repositories.categoria_repository import CategoriaRepository
        
        repo = CategoriaRepository()
        
        # Test get_all
        categorie = repo.get_all()
        print(f"1. Categorie totali: {len(categorie)}")
        for cat in categorie[:5]:  # Prime 5
            print(f"   - {cat}")
        
        # Test create
        nuova_cat = CategoriaTransazione(
            nome_categoria="Test Categoria",
            tipo_macro="Personale"
        )
        cat_salvata = repo.create(nuova_cat)
        print(f"\n2. Nuova categoria salvata con ID: {cat_salvata.id_categoria}")
        
        # Test get_by_tipo_macro
        cat_personali = repo.get_by_tipo_macro("Personale")
        print(f"\n3. Categorie personali: {len(cat_personali)}")
        
        return True
        
    except ImportError:
        print("Repository non ancora implementati - skip test")
        return False
    except Exception as e:
        print(f"Errore nei test repository: {e}")
        return False


def print_next_steps():
    """Stampa i prossimi passi per lo sviluppo."""
    print("\n=== PROSSIMI PASSI ===\n")
    print("1. Implementare tutti i repository (seguendo il pattern in base_repository.py)")
    print("2. Creare i servizi per business logic (SaldoCalculator, ReportGenerator)")
    print("3. Sviluppare la CLI per interazione utente")
    print("4. Aggiungere test unitari per ogni componente")
    print("5. Implementare i report richiesti")
    print("\nConsulta la roadmap dettagliata per l'ordine preciso di implementazione!")


if __name__ == "__main__":
    print("Test Setup Sistema Gestione Finanziaria")
    print("=" * 50)
    
    # Esegui setup
    if setup_test_environment():
        print("\n✅ Setup completato con successo!")
        
        # Testa repository se disponibili
        test_repository_pattern()
    else:
        print("\n❌ Setup fallito - correggere gli errori")
    
    # Mostra prossimi passi
    print_next_steps()
    
    print("\n" + "=" * 50)
    print("Fine test setup")