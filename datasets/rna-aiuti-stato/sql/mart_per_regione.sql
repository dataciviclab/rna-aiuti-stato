-- Aiuti per regione e anno
SELECT
    anno,
    regione_beneficiario,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl
FROM clean_input
WHERE regione_beneficiario != 'ND'
GROUP BY anno, regione_beneficiario
ORDER BY anno DESC, totale_esl DESC
