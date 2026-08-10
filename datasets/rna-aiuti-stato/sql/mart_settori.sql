-- mart_settori — RNA Aiuti di Stato: macro-settore NACE × regione × anno
--
-- Rimpiazza il vecchio mart_settore_regione.
-- Estrae la sezione NACE dal campo settore_attivita e calcola
-- ESL, imprese, quota su regione e ranking.

with settori as (
    select
        anno,
        regione_beneficiario as regione,
        case
            when settore_attivita like '(NACE 2) A.%' then 'A - Agricoltura'
            when settore_attivita like '(NACE 2) B.%' then 'B - Estrazione'
            when settore_attivita like '(NACE 2) C.%' then 'C - Manifatturiero'
            when settore_attivita like '(NACE 2) D.%' then 'D - Energia'
            when settore_attivita like '(NACE 2) E.%' then 'E - Acqua e rifiuti'
            when settore_attivita like '(NACE 2) F.%' then 'F - Costruzioni'
            when settore_attivita like '(NACE 2) G.%' then 'G - Commercio'
            when settore_attivita like '(NACE 2) H.%' then 'H - Trasporti'
            when settore_attivita like '(NACE 2) I.%' then 'I - Servizi alloggio e ristorazione'
            when settore_attivita like '(NACE 2) J.%' then 'J - Informazione e comunicazione'
            when settore_attivita like '(NACE 2) K.%' then 'K - Assicurazioni e credito'
            when settore_attivita like '(NACE 2) L.%' then 'L - Attività immobiliari'
            when settore_attivita like '(NACE 2) M.%' then 'M - Attività professionali'
            when settore_attivita like '(NACE 2) N.%' then 'N - Noleggio e servizi'
            when settore_attivita like '(NACE 2) O.%' then 'O - PA e difesa'
            when settore_attivita like '(NACE 2) P.%' then 'P - Istruzione'
            when settore_attivita like '(NACE 2) Q.%' then 'Q - Sanità'
            when settore_attivita like '(NACE 2) R.%' then 'R - Cultura e sport'
            when settore_attivita like '(NACE 2) S.%' then 'S - Altri servizi'
            else 'Altro / Non classificato'
        end as macro_settore,
        elemento_aiuto,
        codice_fiscale_beneficiario
    from clean_input
    where settore_attivita is not null and settore_attivita != ''
      and regione_beneficiario != 'ND'
)
select
    anno,
    regione,
    macro_settore,
    count(*) as aiuti,
    count(distinct codice_fiscale_beneficiario) as imprese,
    round(sum(elemento_aiuto), 0) as totale_esl,
    round(avg(elemento_aiuto), 0) as media_esl,
    round(sum(elemento_aiuto) * 100.0 / nullif(sum(sum(elemento_aiuto)) over (partition by anno, regione), 0), 2) as quota_pct_su_regione,
    row_number() over (partition by anno, regione order by sum(elemento_aiuto) desc) as rank_in_regione
from settori
where macro_settore != 'Altro / Non classificato'
group by anno, regione, macro_settore
order by anno desc, regione, rank_in_regione;
