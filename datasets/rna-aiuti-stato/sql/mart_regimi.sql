-- mart_regimi — RNA: regimi UE e procedimenti, per anno
-- Lente di lettura: cosa autorizza gli aiuti (regolamento) e come passa (procedimento).

SELECT
    anno,
    COALESCE(NULLIF(TRIM(cod_regolamento), ''), 'ND') AS cod_regolamento,
    CASE
        WHEN cod_regolamento IN ('CE1863-3.2/20', 'CE1863-3.1/20', 'CE1863-3.13/20')
            THEN 'Temporary Crisis Framework (COVID)'
        WHEN cod_regolamento IN ('CE1589/15', 'CE1890-2.2/22', 'CE1890-2.1/22')
            THEN 'Crisi energetica / guerra in Ucraina'
        WHEN cod_regolamento = 'CE651/2014' THEN 'GBER — esenzione generale per categoria'
        WHEN cod_regolamento IN ('CE1407/13', 'CE800/08', 'CE2831/23')
            THEN 'De Minimis'
        WHEN cod_regolamento IN ('CE20122011', 'CE659/1999')
            THEN 'Regimi UE storici / settoriali'
        WHEN cod_regolamento IS NULL OR TRIM(cod_regolamento) = '' THEN 'Non specificato'
        ELSE 'Altro regolamento UE'
    END AS regime,
    COALESCE(NULLIF(TRIM(procedimento), ''), 'ND') AS procedimento,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl,
    ROUND(SUM(elemento_aiuto) * 100.0 / NULLIF(SUM(SUM(elemento_aiuto)) OVER (PARTITION BY anno), 0), 2) AS quota_pct_su_anno
FROM clean_input
GROUP BY
    anno,
    COALESCE(NULLIF(TRIM(cod_regolamento), ''), 'ND'),
    CASE
        WHEN cod_regolamento IN ('CE1863-3.2/20', 'CE1863-3.1/20', 'CE1863-3.13/20')
            THEN 'Temporary Crisis Framework (COVID)'
        WHEN cod_regolamento IN ('CE1589/15', 'CE1890-2.2/22', 'CE1890-2.1/22')
            THEN 'Crisi energetica / guerra in Ucraina'
        WHEN cod_regolamento = 'CE651/2014' THEN 'GBER — esenzione generale per categoria'
        WHEN cod_regolamento IN ('CE1407/13', 'CE800/08', 'CE2831/23')
            THEN 'De Minimis'
        WHEN cod_regolamento IN ('CE20122011', 'CE659/1999')
            THEN 'Regimi UE storici / settoriali'
        WHEN cod_regolamento IS NULL OR TRIM(cod_regolamento) = '' THEN 'Non specificato'
        ELSE 'Altro regolamento UE'
    END,
    COALESCE(NULLIF(TRIM(procedimento), ''), 'ND')
ORDER BY anno DESC, totale_esl DESC
