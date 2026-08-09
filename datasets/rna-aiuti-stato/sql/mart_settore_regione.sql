-- RNA: Aiuti per settore NACE (macro-sezione), regione e anno
-- Estrae la sezione NACE (lettera A-U) dal campo settore_attivita,
-- aggrega ESL, n. aiuti, e calcola ranking del settore per regione.
-- Per vedere quali settori dominano in quali territori.
WITH settori AS (
    SELECT
        anno,
        regione_beneficiario,
        -- Estrae la sezione NACE: '(NACE 2) C.28.2' -> 'C - Manifatturiero'
        CASE
            WHEN settore_attivita LIKE '(NACE 2) A.%' THEN 'A - Agricoltura'
            WHEN settore_attivita LIKE '(NACE 2) B.%' THEN 'B - Estrazione'
            WHEN settore_attivita LIKE '(NACE 2) C.%' THEN 'C - Manifatturiero'
            WHEN settore_attivita LIKE '(NACE 2) D.%' THEN 'D - Energia'
            WHEN settore_attivita LIKE '(NACE 2) E.%' THEN 'E - Acqua e rifiuti'
            WHEN settore_attivita LIKE '(NACE 2) F.%' THEN 'F - Costruzioni'
            WHEN settore_attivita LIKE '(NACE 2) G.%' THEN 'G - Commercio'
            WHEN settore_attivita LIKE '(NACE 2) H.%' THEN 'H - Trasporti'
            WHEN settore_attivita LIKE '(NACE 2) I.%' THEN 'I - Servizi alloggio e ristorazione'
            WHEN settore_attivita LIKE '(NACE 2) J.%' THEN 'J - Informazione e comunicazione'
            WHEN settore_attivita LIKE '(NACE 2) K.%' THEN 'K - Assicurazioni e credito'
            WHEN settore_attivita LIKE '(NACE 2) L.%' THEN 'L - Attività immobiliari'
            WHEN settore_attivita LIKE '(NACE 2) M.%' THEN 'M - Attività professionali'
            WHEN settore_attivita LIKE '(NACE 2) N.%' THEN 'N - Noleggio e servizi'
            WHEN settore_attivita LIKE '(NACE 2) O.%' THEN 'O - PA e difesa'
            WHEN settore_attivita LIKE '(NACE 2) P.%' THEN 'P - Istruzione'
            WHEN settore_attivita LIKE '(NACE 2) Q.%' THEN 'Q - Sanità'
            WHEN settore_attivita LIKE '(NACE 2) R.%' THEN 'R - Cultura e sport'
            WHEN settore_attivita LIKE '(NACE 2) S.%' THEN 'S - Altri servizi'
            ELSE 'Altro / Non classificato'
        END AS macro_settore,
        elemento_aiuto,
        codice_fiscale_beneficiario
    FROM clean_input
    WHERE settore_attivita IS NOT NULL AND settore_attivita != ''
      AND regione_beneficiario != 'ND'
)
SELECT
    anno,
    regione_beneficiario AS regione,
    macro_settore,
    COUNT(*) AS aiuti,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl,
    ROUND(SUM(elemento_aiuto) * 100.0 / NULLIF(SUM(SUM(elemento_aiuto)) OVER (PARTITION BY anno, regione_beneficiario), 0), 2) AS quota_pct_su_regione,
    ROW_NUMBER() OVER (PARTITION BY anno, regione_beneficiario ORDER BY SUM(elemento_aiuto) DESC) AS rank_in_regione
FROM settori
WHERE macro_settore != 'Altro / Non classificato'
GROUP BY anno, regione_beneficiario, macro_settore
ORDER BY anno DESC, regione, rank_in_regione
