-- Aiuti erogati per misura (join con RNA Misure su car)
-- Mostra il plafond della misura (totale_eur) accanto a quanto è stato
-- effettivamente erogato (totale_esl), il n. di imprese e di aiuti.
SELECT
    m.car,
    m.titolo_misura,
    m.des_tipo_misura,
    ROUND(m.importo_prestiti_garantiti, 0) AS plafond_prestiti,
    ROUND(m.importo_aiuto_ad_hoc, 0) AS plafond_aiuto_ad_hoc,
    ROUND(m.importo_prestiti_garantiti + m.importo_aiuto_ad_hoc, 0) AS plafond_totale,
    COUNT(DISTINCT a.codice_fiscale_beneficiario) AS imprese,
    COUNT(*) AS aiuti,
    ROUND(SUM(a.elemento_aiuto), 0) AS totale_esl,
    ROUND(SUM(a.elemento_aiuto) / NULLIF(COUNT(DISTINCT a.codice_fiscale_beneficiario), 0), 0) AS esl_medio_per_impresa
FROM clean_input a
JOIN (
    SELECT car, titolo_misura, des_tipo_misura,
           MAX(importo_prestiti_garantiti) AS importo_prestiti_garantiti,
           MAX(importo_aiuto_ad_hoc) AS importo_aiuto_ad_hoc
    FROM read_parquet('{support.misure.clean}')
    GROUP BY car, titolo_misura, des_tipo_misura
) m ON a.car = m.car
GROUP BY m.car, m.titolo_misura, m.des_tipo_misura,
         m.importo_prestiti_garantiti, m.importo_aiuto_ad_hoc
ORDER BY totale_esl DESC
LIMIT 500