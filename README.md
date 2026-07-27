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

### 1. Via MCP (clean-query) — nessuna installazione

Se usi un ambiente con MCP (AI del Lab o IDE compatibile), puoi interrogare
i dati direttamente in linguaggio naturale: "Quanto aiuto per regione nel 2023?"

### 2. Via DuckDB diretto

```bash
wget https://storage.googleapis.com/dataciviclab-clean/rna/rna_2025.parquet
duckdb -c "SELECT regione_beneficiario,
           ROUND(SUM(elemento_aiuto), 0) AS totale
           FROM 'rna_2025.parquet'
           GROUP BY regione_beneficiario
           ORDER BY totale DESC"
```

### 3. Via download parquet

Tutti i file parquet sono su GCS: `gs://dataciviclab-clean/rna/`

## Approfondimenti

- [Discussion: 11 domande sugli aiuti di Stato](https://github.com/orgs/dataciviclab/discussions/405)
- [Analisi: RNA Aiuti di Stato — 480 miliardi alle imprese in 10 anni](https://github.com/dataciviclab/dataciviclab/tree/main/analisi/rna_aiuti_stato)

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

Schema completo: [docs/schema-misure.md](docs/schema-misure.md)

## Architettura

```
rna-aiuti-stato/
├── rna_aiuti/parser.py     ← parsing, schema, I/O, filtri stream
├── scripts/                ← CI pipeline (full_batch.py, extract.py)
├── tests/                  ← 26 test
├── data/derived/           ← parquet pronti
├── dataset.yml
└── pyproject.toml
```

**Streaming**: download HTTP e parsing XML simultanei, mai un XML su disco.
**Worker**: 4 paralleli, RAM < 500 MB.
**Bootstrap**: 10 anni processati, ~17M righe, CI mensile sull'anno corrente.

## Partecipa

- **Hai una domanda su questi dati?** Apri una [Discussion](https://github.com/orgs/dataciviclab/discussions/new?category=Domanda)
- **Vuoi contribuire al codice?** Vedi [CONTRIBUTING.md](CONTRIBUTING.md)

## Licenza

- **Dati**: CC BY 4.0 (MIMIT)
- **Codice**: MIT
