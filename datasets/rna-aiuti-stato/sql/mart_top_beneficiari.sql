-- Top 1000 beneficiari per totale aiuti ricevuti
SELECT
    codice_fiscale_beneficiario,
    denominazione_beneficiario,
    regione_beneficiario,
    COUNT(*) AS aiuti,
    ROUND(SUM(elemento_aiuto), 0) AS totale_esl,
    ROUND(AVG(elemento_aiuto), 0) AS media_esl
FROM clean_input
WHERE codice_fiscale_beneficiario != ''
GROUP BY codice_fiscale_beneficiario, denominazione_beneficiario, regione_beneficiario
ORDER BY totale_esl DESC
LIMIT 1000
