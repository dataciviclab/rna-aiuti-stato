-- RNA: Aiuti per obiettivo e anno
-- Obiettivo dell'aiuto (cod_obiettivo + descrizione): ESL totale, n. aiuti, n. imprese,
-- peso percentuale sul totale annuale. Mostra come si spostano le priorità di policy.
SELECT
    anno,
    cod_obiettivo,
    obiettivo,
    COUNT(*) AS aiuti,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl,
    -- quota percentuale dell'obiettivo sul totale ESL annuale
    ROUND(SUM(elemento_aiuto) * 100.0 / NULLIF(SUM(SUM(elemento_aiuto)) OVER (PARTITION BY anno), 0), 2) AS quota_pct_su_anno
FROM clean_input
WHERE cod_obiettivo IS NOT NULL AND cod_obiettivo != ''
GROUP BY anno, cod_obiettivo, obiettivo
ORDER BY anno DESC, totale_esl DESC
