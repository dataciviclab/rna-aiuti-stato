# RNA Aiuti di Stato — 17 milioni di aiuti pubblici alle imprese italiane

**480 miliardi di euro in 10 anni. Sai davvero dove sono andati?**

Il Registro Nazionale Aiuti di Stato contiene ogni aiuto pubblico concesso
alle imprese italiane dal 2017: chi lo ha ricevuto, quanto, da chi e per cosa.
Ora è tutto in formato aperto e interrogabile.

## Cosa contiene

| | Aiuti | Misure |
|---|---|---|
| **Cosa** | Singoli aiuti alle imprese | Leggi e regimi che autorizzano gli aiuti |
| **Periodo** | 2017-2026 | 1994-2023 |
| **Righe** | **16.974.895** | 12.874 |
| **Ammontare** | ~480 miliardi di EUR | — |
| **Compressione** | 40 GB XML → 700 MB (58:1) | — |

**Aiuti**: ogni euro pubblico dato alle imprese — beneficiario, importo, concedente,
settore, regione, CUP.

**Misure**: ogni legge, decreto o regime che autorizza aiuti di Stato.

## Esempi di domande

Con questi dati puoi scoprire:

- **Quali regioni italiane ricevono più aiuti di Stato?** E quali settori?
- **Quanto aiuto è andato a imprese della tua città?**
- **Che differenza c'è tra de minimis e notifica?** Quanti aiuti per tipo?
- **Quali leggi hanno autorizzato più aiuti?**
- **Come è cambiato l'importo totale anno per anno?**

## Tre modi per accedere ai dati

### 1. Via MCP (toolkit) — nessuna installazione

I dataset sono pubblicati in formato standard (clean + mart parquet) e
interrogabili con gli strumenti del toolkit del Lab: `toolkit_find`,
`toolkit_dataset_overview`, `toolkit_layer`, `toolkit_registry_show`.

### 2. Via DuckDB diretto

```bash
wget https://storage.googleapis.com/dataciviclab-clean/rna_aiuti_stato/2025/rna_aiuti_stato_2025_clean.parquet
duckdb -c "SELECT regione_beneficiario,
           ROUND(SUM(elemento_aiuto), 0) AS totale
           FROM 'rna_aiuti_stato_2025_clean.parquet'
           GROUP BY regione_beneficiario
           ORDER BY totale DESC"
```

### 3. Via download parquet

Clean e mart pubblicati su GCS (layout year):

- `gs://dataciviclab-clean/rna_aiuti_stato/{year}/`
- `gs://dataciviclab-mart/rna_aiuti_stato/{year}/`
- `gs://dataciviclab-clean/rna_misure/`
- `gs://dataciviclab-mart/rna_misure/`

## Approfondimenti

- [Discussion: 11 domande sugli aiuti di Stato](https://github.com/orgs/dataciviclab/discussions/405)
- [Analisi: RNA Aiuti di Stato — 480 miliardi alle imprese in 10 anni](https://github.com/dataciviclab/dataciviclab/tree/main/analisi/rna-aiuti-stato)

## Schema dati

### Aiuti (31 campi)

```
data_concessione, car, cor              # identificativi
denominazione_beneficiario, ...         # chi
regione_beneficiario                    # dove
soggetto_concedente                     # chi ha erogato
elemento_aiuto, importo_nominale        # quanto (EUR)
procedimento                            # De Minimis / Notifica / Esenzione
settore_attivita                        # NACE Rev.2
strumento                               # Sovvenzione, Prestito, Garanzia
cup, anno, mese                         # partizione
```

### Misure (20 campi)

## Architettura

```
rna-aiuti-stato/
├── rna_aiuti/parser.py       ← parsing XML, schema, I/O, filtri stream
├── scripts/                  ← full_batch.py (XML→parquet)
├── tests/                    ← 26 test
├── data/derived/             ← parquet raw prodotti da full_batch (non in git)
├── datasets/
│   ├── rna-aiuti-stato/      ← dataset.yml + sql/ (clean, 7 mart)
│   └── rna-misure/           ← dataset.yml + sql/ (clean, 3 mart)
├── registry/                 ← registry.json (artifact catalogo, fusion ADR)
└── pyproject.toml
```

**Due fasi**:

1. **Raw** — `full_batch.py` streamma e parsa l'XML RNA.gov.it → parquet in
   `data/derived/` (mai un XML su disco, 4 worker, RAM < 500 MB).
2. **Clean + mart** — il toolkit legge i parquet locali come `local_file` e
   produce i parquet standardizzati + tabelle mart. Solo clean e mart vengono
   pubblicati su GCS; il raw resta locale.

**Registry**: `toolkit registry build --write` genera `registry/registry.json`
(catalogo standard del Lab). **CI**: `pipeline.yml` su runner self-hosted
(full_batch + toolkit + push clean/mart), `check.yml` valida i config su PR,
`test.yml` esegue i test del parser.

## Partecipa

- **Hai una domanda su questi dati?** Apri una [Discussion](https://github.com/orgs/dataciviclab/discussions/new?category=Domanda)
- **Vuoi contribuire al codice?** Vedi [CONTRIBUTING.md](CONTRIBUTING.md)

## Licenza

- **Dati**: CC BY 4.0 (MIMIT)
- **Codice**: MIT
