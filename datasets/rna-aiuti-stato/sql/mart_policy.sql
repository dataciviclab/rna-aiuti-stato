-- mart_policy — RNA Aiuti di Stato: per obiettivo + strumento × anno
--
-- Unifica i vecchi: mart_per_obiettivo + mart_per_strumento.
-- Due sezioni unite dalla colonna `dimensione` (obiettivo/strumento).

select
    anno,
    'obiettivo' as dimensione,
    cod_obiettivo as codice,
    obiettivo as descrizione,
    count(*) as aiuti,
    count(distinct codice_fiscale_beneficiario) as imprese,
    round(sum(elemento_aiuto), 0) as totale_esl,
    round(avg(elemento_aiuto), 0) as media_esl,
    round(sum(elemento_aiuto) * 100.0 / nullif(sum(sum(elemento_aiuto)) over (partition by anno), 0), 2) as quota_pct_su_anno
from clean_input
where cod_obiettivo is not null and cod_obiettivo != ''
group by anno, cod_obiettivo, obiettivo

union all

select
    anno,
    'strumento' as dimensione,
    cod_strumento as codice,
    strumento as descrizione,
    count(*) as aiuti,
    count(distinct codice_fiscale_beneficiario) as imprese,
    round(sum(elemento_aiuto), 0) as totale_esl,
    round(avg(elemento_aiuto), 0) as media_esl,
    round(sum(elemento_aiuto) * 100.0 / nullif(sum(sum(elemento_aiuto)) over (partition by anno), 0), 2) as quota_pct_su_anno
from clean_input
where strumento is not null and strumento != ''
group by anno, cod_strumento, strumento

order by anno desc, dimensione, totale_esl desc;
