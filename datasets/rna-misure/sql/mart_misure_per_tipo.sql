-- mart_misure_per_tipo — Misure di aiuto per tipo
--
-- 1 riga = 1 tipo di misura (Regime di aiuti, Aiuto ad hoc, Regime Quadro):
-- conteggi, prestiti garantiti e aiuti ad hoc (EUR). Serve per:
-- composizione del registro per tipo (D11 #405), peso dei regimi vs ad hoc.
--
-- PK: (des_tipo_misura)

SELECT
    des_tipo_misura,
    COUNT(*) AS n_misure,
    ROUND(SUM(importo_prestiti_garantiti), 0) AS prestiti_garantiti_eur,
    ROUND(SUM(importo_aiuto_ad_hoc), 0) AS aiuto_ad_hoc_eur,
    ROUND(SUM(importo_prestiti_garantiti) + SUM(importo_aiuto_ad_hoc), 0) AS totale_eur
FROM clean_input
WHERE des_tipo_misura IS NOT NULL
GROUP BY des_tipo_misura
ORDER BY totale_eur DESC
