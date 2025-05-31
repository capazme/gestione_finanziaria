-- Schema del database per il sistema di gestione finanziaria e immobiliare
-- Compatibile con SQLite 3.x

-- Abilita foreign keys (disabilitate di default in SQLite)
PRAGMA foreign_keys = ON;

-- Tabella per le proprietà immobiliari
CREATE TABLE IF NOT EXISTS proprieta (
    id_proprieta INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_o_indirizzo_breve TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK(tipo IN ('Possesso ad uso personale', 'Possesso affittata', 'Affitto passivo')),
    data_acquisizione_o_inizio_contratto_affitto TEXT, -- formato YYYY-MM-DD
    valore_acquisto_o_stima_attuale REAL,
    canone_affitto_mensile_attivo REAL,
    canone_affitto_mensile_passivo REAL,
    eventuali_note_legali_o_scadenze_contrattuali TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Trigger per aggiornare updated_at
CREATE TRIGGER IF NOT EXISTS update_proprieta_timestamp 
AFTER UPDATE ON proprieta
BEGIN
    UPDATE proprieta SET updated_at = CURRENT_TIMESTAMP WHERE id_proprieta = NEW.id_proprieta;
END;

-- Indici per ottimizzare le query
CREATE INDEX IF NOT EXISTS idx_proprieta_tipo ON proprieta(tipo);
CREATE INDEX IF NOT EXISTS idx_proprieta_data ON proprieta(data_acquisizione_o_inizio_contratto_affitto);

-- Tabella per i conti finanziari
CREATE TABLE IF NOT EXISTS conto_finanziario (
    id_conto INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_conto TEXT NOT NULL UNIQUE,
    saldo_iniziale REAL NOT NULL DEFAULT 0,
    tipo_conto TEXT NOT NULL CHECK(tipo_conto IN ('Bancario', 'Risparmio', 'Investimento Semplice', 'Contanti')),
    saldo_attuale REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Trigger per aggiornare updated_at
CREATE TRIGGER IF NOT EXISTS update_conto_timestamp 
AFTER UPDATE ON conto_finanziario
BEGIN
    UPDATE conto_finanziario SET updated_at = CURRENT_TIMESTAMP WHERE id_conto = NEW.id_conto;
END;

-- Indice per tipo conto
CREATE INDEX IF NOT EXISTS idx_conto_tipo ON conto_finanziario(tipo_conto);

-- Tabella per le categorie di transazione
CREATE TABLE IF NOT EXISTS categoria_transazione (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_categoria TEXT NOT NULL UNIQUE,
    tipo_macro TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indice per tipo macro categoria
CREATE INDEX IF NOT EXISTS idx_categoria_tipo ON categoria_transazione(tipo_macro);

-- Tabella per le transazioni
CREATE TABLE IF NOT EXISTS transazione (
    id_transazione INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL, -- formato YYYY-MM-DD
    importo REAL NOT NULL CHECK(importo != 0),
    descrizione TEXT NOT NULL,
    id_categoria INTEGER NOT NULL,
    id_conto_finanziario INTEGER NOT NULL,
    id_proprieta_associata INTEGER,
    tipo_flusso TEXT NOT NULL CHECK(tipo_flusso IN ('Personale', 'Immobiliare', 'Fiscale')),
    flag_deducibile_o_rilevante_fiscalmente INTEGER NOT NULL DEFAULT 0 CHECK(flag_deducibile_o_rilevante_fiscalmente IN (0, 1)),
    note_aggiuntive TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_categoria) REFERENCES categoria_transazione(id_categoria) ON DELETE RESTRICT,
    FOREIGN KEY (id_conto_finanziario) REFERENCES conto_finanziario(id_conto) ON DELETE RESTRICT,
    FOREIGN KEY (id_proprieta_associata) REFERENCES proprieta(id_proprieta) ON DELETE SET NULL
);

-- Trigger per aggiornare updated_at
CREATE TRIGGER IF NOT EXISTS update_transazione_timestamp 
AFTER UPDATE ON transazione
BEGIN
    UPDATE transazione SET updated_at = CURRENT_TIMESTAMP WHERE id_transazione = NEW.id_transazione;
END;

-- Indici per ottimizzare le query sulle transazioni
CREATE INDEX IF NOT EXISTS idx_transazione_data ON transazione(data);
CREATE INDEX IF NOT EXISTS idx_transazione_categoria ON transazione(id_categoria);
CREATE INDEX IF NOT EXISTS idx_transazione_conto ON transazione(id_conto_finanziario);
CREATE INDEX IF NOT EXISTS idx_transazione_proprieta ON transazione(id_proprieta_associata);
CREATE INDEX IF NOT EXISTS idx_transazione_tipo_flusso ON transazione(tipo_flusso);
CREATE INDEX IF NOT EXISTS idx_transazione_flag_fiscale ON transazione(flag_deducibile_o_rilevante_fiscalmente);
CREATE INDEX IF NOT EXISTS idx_transazione_data_conto ON transazione(data, id_conto_finanziario);

-- Vista per transazioni con dettagli completi (utile per report)
CREATE VIEW IF NOT EXISTS v_transazioni_dettagliate AS
SELECT 
    t.id_transazione,
    t.data,
    t.importo,
    t.descrizione,
    t.tipo_flusso,
    t.flag_deducibile_o_rilevante_fiscalmente,
    t.note_aggiuntive,
    c.nome_categoria,
    c.tipo_macro,
    cf.nome_conto,
    cf.tipo_conto,
    p.nome_o_indirizzo_breve as nome_proprieta,
    p.tipo as tipo_proprieta,
    CASE 
        WHEN t.importo > 0 THEN 'Entrata'
        ELSE 'Uscita'
    END as direzione_flusso,
    strftime('%Y', t.data) as anno,
    strftime('%m', t.data) as mese,
    strftime('%Y-%m', t.data) as anno_mese
FROM transazione t
JOIN categoria_transazione c ON t.id_categoria = c.id_categoria
JOIN conto_finanziario cf ON t.id_conto_finanziario = cf.id_conto
LEFT JOIN proprieta p ON t.id_proprieta_associata = p.id_proprieta;

-- Vista per saldi conti con totali transazioni
CREATE VIEW IF NOT EXISTS v_saldi_conti AS
SELECT 
    cf.id_conto,
    cf.nome_conto,
    cf.tipo_conto,
    cf.saldo_iniziale,
    cf.saldo_iniziale + COALESCE(SUM(t.importo), 0) as saldo_calcolato,
    cf.saldo_attuale as saldo_registrato,
    COUNT(t.id_transazione) as numero_transazioni,
    MAX(t.data) as ultima_transazione
FROM conto_finanziario cf
LEFT JOIN transazione t ON cf.id_conto = t.id_conto_finanziario
GROUP BY cf.id_conto;

-- Vista per riepilogo proprietà con entrate/uscite
CREATE VIEW IF NOT EXISTS v_riepilogo_proprieta AS
SELECT 
    p.id_proprieta,
    p.nome_o_indirizzo_breve,
    p.tipo,
    p.valore_acquisto_o_stima_attuale,
    p.canone_affitto_mensile_attivo,
    p.canone_affitto_mensile_passivo,
    COUNT(DISTINCT t.id_transazione) as numero_transazioni,
    SUM(CASE WHEN t.importo > 0 THEN t.importo ELSE 0 END) as totale_entrate,
    SUM(CASE WHEN t.importo < 0 THEN ABS(t.importo) ELSE 0 END) as totale_uscite,
    SUM(t.importo) as saldo_netto
FROM proprieta p
LEFT JOIN transazione t ON p.id_proprieta = t.id_proprieta_associata
GROUP BY p.id_proprieta;

-- Tabella per il versionamento dello schema (per future migrazioni)
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Inserisci versione iniziale
INSERT INTO schema_version (version, description) 
VALUES (1, 'Schema iniziale con tabelle base e viste');

-- Tabella per audit log (opzionale ma utile)
CREATE TABLE IF NOT EXISTS audit_log (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    tabella TEXT NOT NULL,
    operazione TEXT NOT NULL CHECK(operazione IN ('INSERT', 'UPDATE', 'DELETE')),
    id_record INTEGER NOT NULL,
    dati_precedenti TEXT, -- JSON con i dati prima della modifica
    dati_nuovi TEXT, -- JSON con i dati dopo la modifica
    utente TEXT DEFAULT 'system',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indice per ricerche nell'audit log
CREATE INDEX IF NOT EXISTS idx_audit_tabella_record ON audit_log(tabella, id_record);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);