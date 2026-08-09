-- mart_territorio — RNA Aiuti di Stato: ESL per regione × anno
--
-- Unifica i vecchi: mart_per_regione + mart_tipo_beneficiario.
-- Per ogni regione: ESL totale, imprese, aiuti, media ESL,
-- quota per tipo beneficiario, benchmark nazionale.

with
regioni as (
    select
        anno,
        regione_beneficiario as regione,
        count(distinct codice_fiscale_beneficiario) as imprese,
        count(*) as aiuti,
        round(sum(elemento_aiuto), 0) as totale_esl,
        round(avg(elemento_aiuto), 0) as media_esl
    from clean_input
    where regione_beneficiario != 'ND'
    group by anno, regione_beneficiario
),
tipi as (
    select
        anno,
        regione_beneficiario as regione,
        tipo_beneficiario,
        count(distinct codice_fiscale_beneficiario) as imprese_tipo,
        round(sum(elemento_aiuto), 0) as esl_tipo,
        round(sum(elemento_aiuto) * 100.0 / nullif(sum(sum(elemento_aiuto)) over (partition by anno, regione_beneficiario), 0), 2) as quota_tipo_pct
    from clean_input
    where regione_beneficiario != 'ND'
      and tipo_beneficiario is not null
      and tipo_beneficiario != '-'
    group by anno, regione_beneficiario, tipo_beneficiario
)
select
    r.*,
    -- Benchmark nazionale per anno
    round(avg(r.totale_esl) over (partition by r.anno), 0) as media_nazionale_esl,
    round(stddev(r.totale_esl) over (partition by r.anno), 0) as std_nazionale_esl,
    case
        when r.totale_esl is null then null
        else round(percent_rank() over (partition by r.anno order by r.totale_esl), 4)
    end as percentile_esl,
    -- Quote per tipo beneficiario (pivot-like)
    max(case when t.tipo_beneficiario = 'PMI' then t.quota_tipo_pct end) as quota_pmi_pct,
    max(case when t.tipo_beneficiario = 'Grande Impresa' then t.quota_tipo_pct end) as quota_grande_pct,
    max(case when t.tipo_beneficiario = 'Microimpresa' then t.quota_tipo_pct end) as quota_micro_pct
from regioni r
left join tipi t on r.anno = t.anno and r.regione = t.regione
group by r.anno, r.regione, r.imprese, r.aiuti, r.totale_esl, r.media_esl
order by r.anno desc, r.totale_esl desc;
