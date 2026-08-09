-- mart_top_misure — Top misure per importo (prestiti garantiti + ad hoc)
--
-- 1 riga = 1 misura: importi totali, tipo, autorità concedente, periodo.
-- Serve per: le misure che hanno erogato di più (D11 #405), top 10,
-- misure con importi rilevanti ancora attive.
-- NOTA: l'importo è il plafond della misura, non l'erogato effettivo
-- (l'erogato si calcola dal join con rna_aiuti_stato via car).
--
-- PK: (car)

SELECT
    car,
    titolo_misura,
    des_tipo_misura,
    des_autorita,
    autorita_concedente,
    data_inizio_misura,
    ROUND(importo_prestiti_garantiti, 0) AS prestiti_garantiti_eur,
    ROUND(importo_aiuto_ad_hoc, 0) AS aiuto_ad_hoc_eur,
    ROUND(importo_prestiti_garantiti + importo_aiuto_ad_hoc, 0) AS totale_eur,
    CASE
        WHEN data_fine_misura IS NULL
             OR data_fine_misura = ''
             OR data_fine_misura LIKE '9999%'
             OR data_fine_misura > '2026-01-01'
        THEN 'attiva' ELSE 'scaduta'
    END AS stato
FROM clean_input
WHERE car IS NOT NULL
ORDER BY totale_eur DESC
