-- RNA: Aiuti per strumento e anno
-- Strumento di aiuto (Sovvenzione, Garanzia, Agevolazione fiscale, Prestito, ...):
-- ESL totale, n. aiuti, peso percentuale e ranking per anno.
-- Aggrega per descrizione strumento (testo): più stabile dei cod_strumento.
SELECT
    anno,
    strumento,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl,
    ROUND(SUM(elemento_aiuto) * 100.0 / NULLIF(SUM(SUM(elemento_aiuto)) OVER (PARTITION BY anno), 0), 2) AS quota_pct_su_anno,
    ROW_NUMBER() OVER (PARTITION BY anno ORDER BY SUM(elemento_aiuto) DESC) AS rank_per_anno
FROM clean_input
WHERE strumento IS NOT NULL AND strumento != ''
GROUP BY anno, strumento
ORDER BY anno DESC, rank_per_anno
