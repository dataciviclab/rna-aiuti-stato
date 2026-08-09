-- Aiuti per tipo di procedimento
SELECT
    anno,
    procedimento,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl
FROM clean_input
WHERE procedimento != ''
GROUP BY anno, procedimento
ORDER BY anno DESC, totale_esl DESC
