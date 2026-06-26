# RNA — Esempi di analisi

Tutte le query su DuckDB. Assumono i parquet in `data/derived/rna/`.

```sql
-- Carica tutti gli anni
CREATE VIEW rna AS
SELECT * FROM read_parquet('data/derived/rna/*.parquet', union_by_name=true);
```

## 1. Quanto aiuto pubblico per regione e anno?

```sql
SELECT anno, regione_beneficiario,
       ROUND(SUM(elemento_aiuto), 0) AS totale_erogato,
       COUNT(DISTINCT codice_fiscale_beneficiario) AS n_imprese
FROM rna
GROUP BY anno, regione_beneficiario
ORDER BY anno, totale_erogato DESC;
```

## 2. De Minimis vs Aiuti notificati: trend annuale

```sql
SELECT anno, procedimento,
       ROUND(SUM(elemento_aiuto), 0) AS totale,
       COUNT(DISTINCT codice_fiscale_beneficiario) AS n_beneficiari
FROM rna
GROUP BY anno, procedimento
ORDER BY anno, totale DESC;
```

## 3. L'azienda X ha preso aiuti pubblici?

```sql
SELECT denominazione_beneficiario, codice_fiscale_beneficiario,
       data_concessione, soggetto_concedente,
       titolo_misura, ROUND(elemento_aiuto, 2) AS importo,
       procedimento, regione_beneficiario
FROM rna
WHERE denominazione_beneficiario LIKE '%COLDIRETTI%'
ORDER BY data_concessione DESC;
```

## 4. Top 10 soggetti concedenti (chi eroga più aiuti?)

```sql
SELECT soggetto_concedente,
       ROUND(SUM(elemento_aiuto), 0) AS totale_erogato,
       COUNT(*) AS n_aiuti,
       COUNT(DISTINCT codice_fiscale_beneficiario) AS n_imprese
FROM rna
WHERE anno = 2023
GROUP BY soggetto_concedente
ORDER BY totale_erogato DESC
LIMIT 10;
```

## 5. Quali settori NACE prendono più aiuti?

```sql
SELECT settore_attivita,
       COUNT(DISTINCT codice_fiscale_beneficiario) AS n_imprese,
       ROUND(SUM(elemento_aiuto), 0) AS totale,
       ROUND(AVG(elemento_aiuto), 2) AS importo_medio
FROM rna
WHERE settore_attivita != '' AND elemento_aiuto IS NOT NULL
GROUP BY settore_attivita
ORDER BY totale DESC
LIMIT 20;
```

## 6. Aiuto pro-capite per regione (con popolazione ISTAT)

```sql
WITH aiuti_regione AS (
    SELECT regione_beneficiario,
           ROUND(SUM(elemento_aiuto), 0) AS totale_aiuti
    FROM rna
    WHERE anno = 2023
    GROUP BY regione_beneficiario
),
popolazione AS (
    SELECT regione, SUM(popolazione) AS residenti
    FROM popolazione_istat
    WHERE anno = 2023
    GROUP BY regione
)
SELECT a.regione_beneficiario,
       a.totale_aiuti,
       p.residenti,
       ROUND(a.totale_aiuti / p.residenti, 2) AS aiuto_procapite
FROM aiuti_regione a
JOIN popolazione p ON a.regione_beneficiario = p.regione
ORDER BY aiuto_procapite DESC;
```

## 7. Imprese che prendono più aiuti contemporaneamente (cumulabilità)

```sql
SELECT codice_fiscale_beneficiario,
       denominazione_beneficiario,
       COUNT(DISTINCT titolo_misura) AS n_misure_distinte,
       ROUND(SUM(elemento_aiuto), 0) AS totale_complessivo
FROM rna
WHERE anno = 2023
GROUP BY codice_fiscale_beneficiario, denominazione_beneficiario
HAVING n_misure_distinte > 5
ORDER BY totale_complessivo DESC;
```

## 8. Trend mensile degli aiuti (stagionalità)

```sql
SELECT anno, mese,
       COUNT(*) AS n_aiuti,
       ROUND(SUM(elemento_aiuto), 0) AS totale_mensile
FROM rna
GROUP BY anno, mese
ORDER BY anno, mese;
```

## 9. Garanzie vs Sovvenzioni: quale strumento predomina?

```sql
SELECT strumento,
       COUNT(*) AS n,
       ROUND(SUM(elemento_aiuto), 0) AS totale,
       ROUND(AVG(elemento_aiuto), 2) AS importo_medio,
       ROUND(SUM(elemento_aiuto) * 100.0 / SUM(SUM(elemento_aiuto)) OVER(), 1) AS percentuale
FROM rna
WHERE strumento != ''
GROUP BY strumento
ORDER BY totale DESC;
```

## 10. CUP presenti vs assenti (tracciabilità progetti)

```sql
SELECT anno,
       SUM(CASE WHEN cup != '' AND cup != 'n.d.' THEN 1 ELSE 0 END) AS con_cup,
       SUM(CASE WHEN cup = '' OR cup = 'n.d.' THEN 1 ELSE 0 END) AS senza_cup,
       ROUND(SUM(CASE WHEN cup != '' AND cup != 'n.d.' THEN elemento_aiuto ELSE 0 END), 0) AS importo_con_cup,
       ROUND(SUM(CASE WHEN cup = '' OR cup = 'n.d.' THEN elemento_aiuto ELSE 0 END), 0) AS importo_senza_cup
FROM rna
GROUP BY anno
ORDER BY anno;
```
