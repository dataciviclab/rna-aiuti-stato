-- RNA Aiuti di Stato — CLEAN
-- I dati sono già puliti dal processo full_batch.py (XML → Parquet).
-- Qui si fa un SELECT * con normalizzazione minima.

SELECT
    data_concessione,
    car,
    cor,
    denominazione_beneficiario,
    codice_fiscale_beneficiario,
    tipo_beneficiario,
    COALESCE(NULLIF(regione_beneficiario, ''), 'ND') AS regione_beneficiario,
    soggetto_concedente,
    titolo_misura,
    des_tipo_misura,
    titolo_progetto,
    descrizione_progetto,
    cup,
    atto_concessione,
    base_giuridica_nazionale,
    identificativo_ufficio,
    link_trasparenza_nazionale,
    id_componente,
    procedimento,
    cod_procedimento,
    regolamento_ue,
    cod_regolamento,
    obiettivo,
    cod_obiettivo,
    settore_attivita,
    cod_strumento,
    strumento,
    elemento_aiuto,
    importo_nominale,
    anno,
    mese
FROM raw_input
WHERE elemento_aiuto IS NOT NULL
