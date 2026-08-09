-- mart_misure_attive — Misure ancora attive per anno di inizio
--
-- 1 riga = 1 anno di inizio validità: totale misure create, di cui ancora
-- attive (fine validità nel futuro o data aperta 9999). Serve per:
-- misure "dimenticate" ma ancora in vigore (D11 #405).
--
-- PK: (anno)

SELECT
    anno,
    COUNT(*) AS n_misure_istituite,
    SUM(
        CASE
            WHEN data_fine_misura IS NULL
                 OR data_fine_misura = ''
                 OR data_fine_misura LIKE '9999%'
                 OR data_fine_misura > '2026-01-01'
            THEN 1 ELSE 0
        END
    ) AS ancora_attive,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN data_fine_misura IS NULL
                     OR data_fine_misura = ''
                     OR data_fine_misura LIKE '9999%'
                     OR data_fine_misura > '2026-01-01'
                THEN 1 ELSE 0
            END
        ) / NULLIF(COUNT(*), 0),
        1
    ) AS quota_attive_pct
FROM clean_input
WHERE anno IS NOT NULL
GROUP BY anno
ORDER BY anno DESC
