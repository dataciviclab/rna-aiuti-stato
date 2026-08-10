-- RNA: Aiuti per tipo beneficiario, regione e anno
-- PMI vs Grande impresa vs Non classificata: ESL, n. imprese, media ESL,
-- quote percentuali per regione e anno. Mostra la distribuzione degli aiuti
-- tra tipologie di impresa.
SELECT
    anno,
    tipo_beneficiario,
    regione_beneficiario,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl,
    ROUND(SUM(elemento_aiuto) * 100.0 / NULLIF(SUM(SUM(elemento_aiuto)) OVER (PARTITION BY anno, regione_beneficiario), 0), 2) AS quota_pct_su_regione
FROM clean_input
WHERE tipo_beneficiario IS NOT NULL
  AND tipo_beneficiario != '-'
  AND regione_beneficiario != 'ND'
GROUP BY anno, tipo_beneficiario, regione_beneficiario
ORDER BY anno DESC, regione_beneficiario, totale_esl DESC
