-- mart_concentrazione — RNA: distribuzione del valore per beneficiario
-- Bucket di importo totale ricevuto (per CF) × anno: pareto, non la media.

WITH per_cf AS (
    SELECT
        anno,
        codice_fiscale_beneficiario,
        COUNT(*) AS n_aiuti,
        ROUND(SUM(elemento_aiuto), 0) AS totale_esl
    FROM clean_input
    WHERE codice_fiscale_beneficiario IS NOT NULL
      AND TRIM(codice_fiscale_beneficiario) != ''
    GROUP BY anno, codice_fiscale_beneficiario
)
SELECT
    anno,
    CASE
        WHEN totale_esl >= 10000000 THEN '>=10M'
        WHEN totale_esl >= 1000000 THEN '1M-10M'
        WHEN totale_esl >= 100000 THEN '100k-1M'
        WHEN totale_esl >= 10000 THEN '10k-100k'
        ELSE '<10k'
    END AS bucket_importo,
    COUNT(*) AS n_imprese,
    SUM(n_aiuti) AS aiuti,
    ROUND(SUM(totale_esl), 0) AS totale_esl,
    ROUND(SUM(totale_esl) * 100.0 / NULLIF(SUM(SUM(totale_esl)) OVER (PARTITION BY anno), 0), 2) AS quota_importo_pct,
    ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY anno), 0), 4) AS quota_imprese_pct
FROM per_cf
GROUP BY anno, 2
ORDER BY anno DESC, totale_esl DESC
