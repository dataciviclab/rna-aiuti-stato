# RNA Aiuti di Stato — Registro Nazionale Aiuti di Stato

**Ogni aiuto pubblico concesso alle imprese italiane, in formato queryabile.**

## Cosa contiene

| | Aiuti | Misure |
|---|---|---|
| Cosa | Singoli aiuti alle imprese | Leggi/regimi che autorizzano gli aiuti |
| Periodo | 2017-oggi | 1994-2023 |
| File XML | 114 | ~237 |
| Righe | ~4M (e cresce) | ~13K |
| Parquet | Annuale (`rna_YYYY.parquet`) | Unico (`misure.parquet`) |

**Aiuti**: ogni euro pubblico dato alle imprese — beneficiario, importo, concedente, settore, regione, CUP.

**Misure**: ogni legge, decreto o regime che autorizza aiuti di Stato — `car`, titolo, base giuridica, autorità concedente, date validità.

### Schema Aiuti (31 campi)

Una riga = una combinazione **Aiuto × Componente × Strumento**.

```
data_concessione, car, cor          # identificativi
denominazione_beneficiario, codice_fiscale_beneficiario  # chi
regione_beneficiario               # dove
soggetto_concedente                # chi ha erogato
elemento_aiuto, importo_nominale   # quanto (EUR)
procedimento                       # De Minimis / Notifica / Esenzione
settore_attivita                   # NACE Rev.2
strumento                          # Sovvenzione, Prestito, Garanzia
cup                                # Codice Unico di Progetto
anno, mese                         # partizione
```

### Schema Misure (20 campi)

```
car                                # codice misura (PK)
titolo_misura, des_tipo_misura     # descrizione
data_inizio_misura, data_fine_misura  # validità
base_giuridica_nazionale           # legge/ decreto
cod_amm, des_autorita              # ente
importo_prestiti_garantiti, importo_aiuto_ad_hoc  # importi
```

## Uso rapido

```bash
pip install -e ".[dev]"

# Aiuti — per anno
python3 scripts/full_batch.py --from 2023 --to 2023

# Aiuti — tutti gli anni
python3 scripts/full_batch.py --full

# Misure — tutte (237 file, ~1 minuto)
python3 scripts/full_batch.py --misure

# Summary
python3 scripts/full_batch.py --summary
python3 scripts/generate_manifest.py
```

### Query esempio

```sql
-- Quanto aiuto per regione nel 2023?
SELECT regione_beneficiario, ROUND(SUM(elemento_aiuto), 0) AS totale
FROM 'data/derived/rna/rna_*.parquet'
WHERE anno = 2023
GROUP BY regione_beneficiario ORDER BY totale DESC

-- Aiuti per tipo procedimento
SELECT procedimento, COUNT(*) AS aiuti, ROUND(SUM(elemento_aiuto), 0) AS totale
FROM 'data/derived/rna/rna_*.parquet'
GROUP BY procedimento

-- Misure: quante per anno?
SELECT anno, COUNT(*) AS misure
FROM 'data/derived/misure/misure.parquet'
GROUP BY anno ORDER BY anno
```

## Architettura

```
rna-aiuti-stato/
├── rna_aiuti/
│   ├── __init__.py
│   └── parser.py              ← parsing, schema, I/O, filtri stream
├── scripts/
│   ├── full_batch.py           ← CI pipeline: worker paralleli, aiuti + misure
│   ├── extract.py              ← CLI per singolo file (thin)
│   └── generate_manifest.py    ← manifest annuali + index
├── tests/
│   └── test_parser.py          ← 26 test
├── data/
│   ├── derived/rna/            ← parquet annuali Aiuti
│   ├── derived/misure/         ← parquet unico Misure
│   └── derived/manifests/      ← manifest JSON per anno
├── dataset.yml
└── pyproject.toml
```

**Streaming**: download HTTP e parsing XML simultanei — mai un XML scritto su disco.

**Worker**: 2 di default (picco RAM < 500 MB con 2 worker paralleli). Su VM con 12 GB si può salire a 4.

**Manifest**: ogni anno completato genera `manifests/rna_YYYY.json` + `rna_index.json` cumulativo. La CI li committa su main.

**Robustezza**: `XMLCharFilter` (byte non validi) + `XMLTagFixer` (tag troncati) in cascata sullo stream.

## CI

Workflow `build` su self-hosted runner (Oracle Cloud ARM64, 2 OCPU, 12 GB RAM). Processa un anno alla volta (`--from YYYY --to YYYY`). Output su GCS + commit manifest.

## Licenza

- **Dati**: CC BY 4.0 (MIMIT)
- **Codice**: MIT
