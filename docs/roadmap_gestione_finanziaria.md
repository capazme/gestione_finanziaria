# Roadmap Dettagliata - Sistema Gestione Finanziaria e Immobiliare (AGGIORNATA)

## 📋 Overview del Progetto

Sistema di gestione finanziaria personale e immobiliare con focus su:

* Tracking finanze personali
* Gestione rendimenti/costi proprietà immobiliari
* Preparazione dati per dichiarazione dei redditi
* Analisi cash flow e redditività

## 🏗️ Struttura del Progetto

```
gestione_finanziaria/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── proprieta.py
│   │   ├── conto_finanziario.py
│   │   ├── categoria_transazione.py
│   │   └── transazione.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── schema.sql
│   │   └── migrations.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── proprieta_repository.py
│   │   ├── conto_repository.py
│   │   ├── categoria_repository.py
│   │   └── transazione_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── saldo_calculator.py
│   │   ├── report_generator.py
│   │   └── validation_service.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── proprieta_commands.py
│   │   │   ├── conto_commands.py
│   │   │   ├── categoria_commands.py
│   │   │   ├── transazione_commands.py
│   │   │   └── report_commands.py
│   │   └── utils.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── tests/
│   ├── __init__.py
│   ├── test_models/
│   ├── test_repositories/
│   ├── test_services/
│   └── test_cli/
├── data/
│   └── database.db (generato automaticamente)
├── docs/
│   ├── user_guide.md
│   └── api_reference.md
├── requirements.txt
├── setup.py
├── README.md
└── .gitignore
```

## 🚀 Fasi di Implementazione

### FASE 1: Setup Iniziale e Modelli

- [✓] Creare struttura directory del progetto
- [✓] Inizializzare repository git
- [✓] Creare virtual environment Python
- [✓] Installare dipendenze base (sqlite3 è built-in)
- [✓] Configurare .gitignore

#### 1.2 Definizione Modelli Dati

- [✓] Implementare dataclass `Proprieta` con tutti i campi specificati
- [✓] Implementare dataclass `ContoFinanziario`
- [✓] Implementare dataclass `CategoriaTransazione`
- [✓] Implementare dataclass `Transazione`
- [✓] Aggiungere metodi di validazione base per ogni modello
- [✓] Implementare metodi `__str__` e `__repr__` per output leggibili

### FASE 2: Database Layer

#### 2.1 Setup Database

- [✓] Creare modulo `connection.py` per gestione connessione SQLite
- [✓] Implementare context manager per transazioni sicure
- [✓] Creare file `schema.sql` con definizioni tabelle
- [✓] Implementare funzione `create_database()` che esegue schema.sql
- [✓] Aggiungere indici per ottimizzare query comuni

#### 2.2 Sistema di Migrazione

- [ ] Implementare sistema base per tracking versioni schema
- [ ] Creare prima migrazione con schema iniziale
- [ ] Implementare funzione per verificare/aggiornare schema

### FASE 3: Repository Pattern

#### 3.1 Base Repository

- [✓] Creare classe astratta `BaseRepository` con metodi CRUD comuni
- [✓] Implementare gestione errori e logging

#### 3.2 Repository Specifici

- [✓] `CategoriaRepository`:
  - [✓] `create()` - con validazione unicità nome
  - [✓] `get_by_id()`, `get_by_nome()`
  - [✓] `get_all()` con filtri per tipo_macro
  - [✓] `update()`, `delete()` con controllo dipendenze
- [✓] `ContoRepository`:
  - [✓] CRUD completo con validazione
  - [✓] `get_by_tipo()` per filtrare per tipo conto
  - [✓] Metodo per batch update saldi
- [✓] `ProprietaRepository`:
  - [✓] CRUD con validazione date e importi
  - [✓] `get_proprieta_attive()` per proprietà affittate
  - [✓] `get_proprieta_per_tipo()`
- [✓] `TransazioneRepository`:
  - [✓] CRUD con validazione referenze FK
  - [✓] `get_by_periodo()` con filtri data
  - [✓] `get_by_conto()`, `get_by_proprieta()`
  - [✓] `get_by_categoria()` con aggregazioni

### FASE 4: Business Logic

#### 4.1 Servizio Calcolo Saldi

- [✓] Implementare `SaldoCalculator`:
  - [✓] `calcola_saldo_conto()` - ricalcola da saldo iniziale
  - [✓] `aggiorna_saldo_dopo_transazione()` - update incrementale
  - [✓] `verifica_coerenza_saldi()` - controllo integrità
  - [✓] Gestione transazioni atomiche per consistenza

#### 4.2 Servizio Validazione

- [ ] `ValidationService`:
  - [ ] Validazione date (formato, coerenza temporale)
  - [ ] Validazione importi (non null, decimali corretti)
  - [ ] Validazione referenze (FK esistenti)
  - [ ] Validazione business rules (es. proprietà affittata deve avere canone)

### FASE 5: Report Generator

#### 5.1 Report Cash Flow Personale

- [✓] Implementare `generate_cash_flow_personale()`:
  - [✓] Parametri: mese/anno, formato output (dict/csv)
  - [✓] Calcolo entrate personali (escludendo immobiliari)
  - [✓] Calcolo uscite personali (includendo affitto passivo)
  - [✓] Calcolo risparmio/deficit
  - [ ] Breakdown per categoria (opzionale, non MVP)

#### 5.2 Report P&L Proprietà

- [✓] Implementare `generate_pl_proprieta()`:
  - [✓] Parametri: id_proprieta, periodo, formato
  - [✓] Entrate da affitti
  - [✓] Spese dirette (mutuo, tasse, manutenzione)
  - [✓] Calcolo margine operativo
  - [ ] Trend mensili se richiesto (opzionale)

#### 5.3 Report Fiscale

- [✓] Implementare `generate_riepilogo_fiscale()`:
  - [✓] Filtraggio transazioni deducibili
  - [✓] Raggruppamento per tipologia fiscale
  - [✓] Riepilogo entrate da locazione per proprietà
  - [ ] Export formato compatibile commercialista (opzionale)

#### 5.4 Report Patrimonio

- [✓] Implementare `calculate_patrimonio_netto_semplificato()`:
  - [✓] Somma valori proprietà
  - [✓] Somma saldi conti
  - [✓] Stima debiti residui (placeholder per ora)
  - [✓] Snapshot con timestamp

### FASE 6: CLI Interface

#### 6.1 Setup CLI Base

- [ ] Configurare menu principale con opzioni numeriche
- [ ] Implementare navigazione gerarchica
- [ ] Aggiungere help contestuale
- [ ] Gestione errori user-friendly

#### 6.2 Comandi Proprietà

- [ ] Menu gestione proprietà: aggiungi, visualizza, modifica, elimina

#### 6.3 Comandi Conti

- [ ] Menu gestione conti: aggiungi, visualizza, modifica, riconciliazione

#### 6.4 Comandi Categorie

- [ ] Setup categorie predefinite, aggiungi, visualizza, modifica/elimina

#### 6.5 Comandi Transazioni

- [ ] Inserimento rapido, ricerca, modifica/elimina

#### 6.6 Menu Report

- [ ] Selezione tipo report, input parametri, visualizzazione, export CSV

### FASE 7: Testing e Documentazione

- [~] Test modelli, repository, servizi (parzialmente presenti)
- [ ] Test CLI
- [ ] README, guida utente, esempi

## 📊 Metriche di Successo MVP

* [ ] Gestione completa CRUD per tutte le entità
* [ ] Calcolo saldi automatico e coerente
* [ ] Almeno 4 report funzionanti
* [ ] CLI utilizzabile senza documentazione
* [ ] Zero crash su operazioni standard
* [ ] Backup dati affidabile

## 🔄 Iterazioni Future (Post-MVP)

1. **v1.1 - Enhanced Reporting**
   * Dashboard riepilogativo
   * Grafici ASCII in CLI
   * Export PDF report
2. **v1.2 - Automazioni**
   * Import transazioni da CSV banca
   * Notifiche scadenze
   * Calcolo ROI proprietà
3. **v1.3 - Web Interface**
   * API REST con FastAPI
   * Frontend React semplice
   * Multi-utente con auth
4. **v2.0 - Advanced Features**
   * Integrazione servizi esterni
   * Machine learning per categorizzazione
   * Simulazioni e proiezioni

## 💡 Best Practices da Seguire

1. **Codice** : Type hints ovunque, docstrings dettagliate
2. **Database** : Transazioni ACID, backup prima di operazioni distruttive
3. **UX** : Conferme per operazioni distruttive, messaggi chiari
4. **Testing** : Test prima di ogni commit importante
5. **Git** : Commit atomici con messaggi descrittivi

## 🚨 Rischi e Mitigazioni

| Rischio                    | Probabilità | Impatto | Mitigazione                             |
| -------------------------- | ------------ | ------- | --------------------------------------- |
| Corruzione database        | Bassa        | Alto    | Backup automatici, transazioni atomiche |
| Errori calcolo fiscale     | Media        | Alto    | Validazione input, test estensivi       |
| Complessità UX            | Media        | Medio   | Wizard guidati, help contestuale        |
| Performance con molti dati | Bassa        | Basso   | Indici DB, paginazione risultati        |

## ✅ Definition of Done per MVP

* [ ] Tutte le funzionalità CRUD implementate e testate
* [ ] Report generano output corretti con dati di test
* [ ] CLI navigabile senza errori
* [ ] Documentazione base completa
* [ ] Nessun TODO critico nel codice
* [ ] Database gestisce correttamente concorrenza

**Prossimi step consigliati:**  
- Completare la CLI (Fase 6) per permettere l'interazione utente.
- Rafforzare la validazione e i test automatici.
- Migliorare la documentazione e l'esperienza utente.
