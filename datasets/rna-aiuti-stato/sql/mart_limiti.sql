-- mart_limiti — RNA: indicatori di qualità / copertura, per anno
-- CUP n.d., regione multipla, importi zero: il caveat è parte del dato.

SELECT
    anno,
    COUNT(*) AS aiuti,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    SUM(CASE WHEN cup IS NULL OR TRIM(cup) = '' OR cup = 'n.d.' THEN 1 ELSE 0 END) AS senza_cup,
    ROUND(
        SUM(CASE WHEN cup IS NULL OR TRIM(cup) = '' OR cup = 'n.d.' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 2
    ) AS pct_senza_cup,
    SUM(CASE WHEN regione_beneficiario IS NULL OR regione_beneficiario = 'ND' THEN 1 ELSE 0 END) AS regione_nd,
    SUM(CASE WHEN regione_beneficiario LIKE '%,%' THEN 1 ELSE 0 END) AS regione_multi,
    ROUND(
        SUM(CASE WHEN regione_beneficiario LIKE '%,%' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 2
    ) AS pct_regione_multi,
    SUM(CASE WHEN elemento_aiuto IS NULL OR elemento_aiuto = 0 THEN 1 ELSE 0 END) AS importo_null_o_zero,
    ROUND(
        SUM(CASE WHEN elemento_aiuto IS NULL OR elemento_aiuto = 0 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 2
    ) AS pct_importo_null_o_zero
FROM clean_input
GROUP BY anno
ORDER BY anno
