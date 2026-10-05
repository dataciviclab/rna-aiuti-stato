-- mart_concedenti — RNA: chi eroga, per anno
-- Volume (n. aiuti) vs valore (ESL) per soggetto concedente,
-- con tipologia semantica (garanzia, INPS, energia, enti locali...).

WITH raw AS (
    SELECT
        anno,
        COALESCE(NULLIF(TRIM(soggetto_concedente), ''), 'Non specificato') AS soggetto_concedente,
        elemento_aiuto,
        codice_fiscale_beneficiario
    FROM clean_input
),
norm AS (
    SELECT
        anno,
        soggetto_concedente,
        LOWER(soggetto_concedente) AS k,
        elemento_aiuto,
        codice_fiscale_beneficiario
    FROM raw
),
agg AS (
    SELECT
        anno,
        soggetto_concedente,
        CASE
            WHEN k LIKE '%mediocredito%' OR k LIKE '%mezzogiorno%' THEN 'Garanzia / MCC'
            WHEN k LIKE '%sace%' THEN 'Garanzia / SACE'
            WHEN k LIKE '%inps%' THEN 'INPS / contributivi'
            WHEN k LIKE '%agenzia delle entrate%' OR k LIKE '%agenzie delle entrate%' THEN 'Agenzia Entrate'
            WHEN k LIKE '%gse%' OR k LIKE '%gestore servizi energetici%' THEN 'Energia / GSE'
            WHEN k LIKE '%terna%' THEN 'Energia / Terna'
            WHEN k LIKE '%regione%' OR k LIKE '%provincia%' OR k LIKE '%comune%'
                 OR k LIKE '%camdi%' OR k LIKE '%camera di commercio%' THEN 'Enti locali / CCI'
            WHEN k LIKE '%ministero%' OR k LIKE '%mimit%' OR k LIKE '%invitalia%' THEN 'Stato / Invitalia'
            WHEN k LIKE '%fondimpresa%' OR k LIKE '%formazienda%' OR k LIKE '%fondoprofessioni%'
                 OR k LIKE '%fondo%' OR k LIKE '%fonarcom%' OR k LIKE '%fondi%' THEN 'Fondi interprofessionali'
            ELSE 'Altri'
        END AS tipo_concedente,
        COUNT(*) AS aiuti,
        ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
        COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese
    FROM norm
    GROUP BY anno, soggetto_concedente,
        CASE
            WHEN k LIKE '%mediocredito%' OR k LIKE '%mezzogiorno%' THEN 'Garanzia / MCC'
            WHEN k LIKE '%sace%' THEN 'Garanzia / SACE'
            WHEN k LIKE '%inps%' THEN 'INPS / contributivi'
            WHEN k LIKE '%agenzia delle entrate%' OR k LIKE '%agenzie delle entrate%' THEN 'Agenzia Entrate'
            WHEN k LIKE '%gse%' OR k LIKE '%gestore servizi energetici%' THEN 'Energia / GSE'
            WHEN k LIKE '%terna%' THEN 'Energia / Terna'
            WHEN k LIKE '%regione%' OR k LIKE '%provincia%' OR k LIKE '%comune%'
                 OR k LIKE '%camdi%' OR k LIKE '%camera di commercio%' THEN 'Enti locali / CCI'
            WHEN k LIKE '%ministero%' OR k LIKE '%mimit%' OR k LIKE '%invitalia%' THEN 'Stato / Invitalia'
            WHEN k LIKE '%fondimpresa%' OR k LIKE '%formazienda%' OR k LIKE '%fondoprofessioni%'
                 OR k LIKE '%fondo%' OR k LIKE '%fonarcom%' OR k LIKE '%fondi%' THEN 'Fondi interprofessionali'
            ELSE 'Altri'
        END
)
SELECT
    anno,
    soggetto_concedente,
    tipo_concedente,
    aiuti,
    totale_esl,
    imprese,
    ROUND(totale_esl * 100.0 / NULLIF(SUM(totale_esl) OVER (PARTITION BY anno), 0), 2) AS quota_pct_su_anno,
    ROUND(totale_esl * 100.0 / NULLIF(SUM(totale_esl) OVER (PARTITION BY anno, tipo_concedente), 0), 2) AS quota_pct_su_tipo,
    ROW_NUMBER() OVER (PARTITION BY anno ORDER BY totale_esl DESC) AS rank_per_anno,
    ROW_NUMBER() OVER (PARTITION BY anno, tipo_concedente ORDER BY totale_esl DESC) AS rank_in_tipo
FROM agg
ORDER BY anno DESC, rank_per_anno
