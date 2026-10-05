-- mart_temporale — RNA: serie mensili per anno e procedimento
-- Stagionalità, spike COVID/energia, ritmo delle concessioni.

SELECT
    anno,
    mese,
    COALESCE(NULLIF(TRIM(procedimento), ''), 'ND') AS procedimento,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl
FROM clean_input
WHERE mese IS NOT NULL AND mese BETWEEN 1 AND 12
GROUP BY anno, mese, 3
ORDER BY anno, mese, totale_esl DESC
