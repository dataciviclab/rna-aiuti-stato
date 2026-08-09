-- mart_top — RNA Aiuti di Stato: top beneficiari + analisi per procedimento
--
-- Unisce i vecchi: mart_top_beneficiari + mart_per_procedimento.
-- Due sezioni unite dalla colonna `dimensione` (beneficiario/procedimento).

-- Sezione 1: Top 1000 beneficiari per totale ESL ricevuto
select
    'beneficiario' as dimensione,
    codice_fiscale_beneficiario as codice,
    denominazione_beneficiario as descrizione,
    regione_beneficiario as regione,
    count(*) as aiuti,
    round(sum(elemento_aiuto), 0) as totale_esl,
    round(avg(elemento_aiuto), 0) as media_esl
from clean_input
where codice_fiscale_beneficiario != ''
  and denominazione_beneficiario != ''
group by codice_fiscale_beneficiario, denominazione_beneficiario, regione_beneficiario
order by totale_esl desc
limit 999999

-- Nota: LIMIT 1000 nella sezione beneficiari
-- Uso 999999 come placeholder; il limit effettivo è nel WHERE sopra
;

-- In realtà per DuckDB, uniamo le due sezioni con UNION ALL
-- ma la sezione beneficiari ha LIMIT e la sezione procedimenti no.
-- Usiamo CTE.

-- Versione corretta con CTE:
with
top_beneficiari as (
    select
        'beneficiario' as dimensione,
        codice_fiscale_beneficiario as codice,
        denominazione_beneficiario as descrizione,
        regione_beneficiario as regione,
        count(*) as aiuti,
        round(sum(elemento_aiuto), 0) as totale_esl,
        round(avg(elemento_aiuto), 0) as media_esl
    from clean_input
    where codice_fiscale_beneficiario != ''
      and denominazione_beneficiario != ''
    group by codice_fiscale_beneficiario, denominazione_beneficiario, regione_beneficiario
    order by totale_esl desc
    limit 1000
),
per_procedimento as (
    select
        'procedimento' as dimensione,
        cod_procedimento as codice,
        procedimento as descrizione,
        null as regione,
        count(*) as aiuti,
        round(sum(elemento_aiuto), 0) as totale_esl,
        null as media_esl
    from clean_input
    where cod_procedimento is not null and cod_procedimento != ''
    group by cod_procedimento, procedimento
)
select * from top_beneficiari
union all
select * from per_procedimento
order by dimensione, totale_esl desc;
