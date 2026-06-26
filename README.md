# RNA Aiuti di Stato — Registro Nazionale Aiuti di Stato

**Ogni aiuto pubblico concesso alle imprese italiane, in formato queryabile.**

Questo progetto estrae i dati del [Registro Nazionale Aiuti di Stato](https://www.rna.gov.it/) (MIMIT) dal formato XML nativo a **Parquet**, zero perdite, zero storage raw intermedio. Dal 2017 a oggi, ogni aiuto concesso con beneficiario, importo, settore e concedente.

## Cosa contiene

| | 2017 (completo) |
|---|---|
| File XML sorgente | 12 file, ~3 GB |
| Parquet finale | **11 MB** (compressione 270:1) |
| Aiuti | 216.931 |
| Beneficiari unici | decine di migliaia |
| Concedenti | Ministeri, Regioni, Camere di Commercio, INPS, INAIL, … |

### Schema (31 campi)

Una riga = una combinazione **Aiuto × Componente × Strumento**.

```
data_concessione         # quando
car, cor                # codici identificativi
denominazione_beneficiario  # chi (ragione sociale)
codice_fiscale_beneficiario # chi (CF/P.IVA)
tipo_beneficiario        # PMI, Grande impresa, …
regione_beneficiario     # dove
soggetto_concedente      # chi ha erogato
titolo_misura            # per cosa (legge/regime)
elemento_aiuto           # quanto (EUR) — ESL effettivo
importo_nominale         # quanto (EUR) — valore operazione
procedimento             # De Minimis / Notifica / Esenzione
settore_attivita         # NACE Rev.2 (es. J.62.0 software)
strumento                # Sovvenzione, Prestito, Garanzia, …
cup                      # Codice Unico di Progetto
anno, mese               # partizione
```

Vedi [dataset.yml](dataset.yml) per lo schema completo.

## Perché è unico

- **Nessuno in Italia** ha questi dati in formato queryabile. Il RNA esiste solo come 133 file XML mensili sul sito del MIMIT.
- **Traccia ogni euro pubblico** dato alle imprese: dai microprestiti De Minimis alle grandi esenzioni notificate.
- **Incrociabile** con ANAC (gare), ADE (redditi), MEF (partecipate), ISTAT (popolazione).

## Uso rapido

```bash
# Installa il pacchetto (obbligatorio prima del primo uso)
pip install -e ".[dev]"

# Summary dei parquet già processati
python3 scripts/full_batch.py --summary

# Estrai un periodo in streaming parallelo (4 worker, RAM < 500 MB)
python3 scripts/full_batch.py --from 2023 --to 2025

# Full (tutti i 114 file, ~3 ore con 4 worker)
python3 scripts/full_batch.py --full
```

### Query esempio

```sql
-- Quanto aiuto per regione?
SELECT regione_beneficiario, ROUND(SUM(elemento_aiuto), 0) AS totale
FROM 'data/derived/rna/rna_*.parquet'
WHERE anno = 2023
GROUP BY regione_beneficiario
ORDER BY totale DESC

-- I 10 maggiori beneficiari
SELECT denominazione_beneficiario, codice_fiscale_beneficiario,
       ROUND(SUM(elemento_aiuto), 2) AS totale
FROM 'data/derived/rna/rna_*.parquet'
GROUP BY denominazione_beneficiario, codice_fiscale_beneficiario
ORDER BY totale DESC
LIMIT 10

-- De Minimis vs notificati per anno
SELECT anno, procedimento, ROUND(SUM(elemento_aiuto), 0) AS totale
FROM 'data/derived/rna/rna_*.parquet'
GROUP BY anno, procedimento
ORDER BY anno, totale DESC

-- Settori NACE che prendono più aiuti
SELECT settore_attivita, COUNT(DISTINCT codice_fiscale_beneficiario) AS imprese,
       ROUND(SUM(elemento_aiuto), 0) AS totale
FROM 'data/derived/rna/rna_*.parquet'
WHERE settore_attivita != ''
GROUP BY settore_attivita
ORDER BY totale DESC
```

## Architettura

```
rna-aiuti-stato/
├── rna_aiuti/
│   ├── __init__.py          ← API pubblica del pacchetto
│   └── parser.py            ← SINGLE SOURCE OF TRUTH: parsing XML puro,
│                               schema PyArrow, I/O parquet, filtri stream
├── scripts/
│   ├── extract.py           ← CLI per singolo file / batch locale (thin)
│   └── full_batch.py        ← CI pipeline: download HTTP streaming + workers
├── tests/
│   └── test_parser.py       ← 20 test: parsing, schema, stream filter, I/O
├── data/
│   ├── raw/                 ← NON in git (solo cache opzionale)
│   └── derived/rna/         ← parquet annuali (rna_YYYY.parquet)
├── dataset.yml              ← catalogo Lab
├── pyproject.toml
└── README.md
```

**Streaming**: il download HTTP e il parsing XML avvengono contemporaneamente — nessun file XML viene mai scritto su disco. `lxml.iterparse` processa un `<AIUTO>` alla volta mentre `urllib` scarica il resto.

**Parallelismo**: i file mensili sono indipendenti → `ThreadPoolExecutor` con 4 worker. La memoria non accumula dati: ogni file viene scritto subito su disco (append per anno), il picco RAM è sotto 500 MB anche con 4 worker paralleli.

**Storage finale**: ~50 MB per anno di parquet (vs ~5-10 GB di XML sorgente). Compressione media 100:1-200:1.

**Scrittura incrementale**: a ogni run, i parquet degli anni richiesti vengono ricreati da zero (cleanup iniziale + append per mese). Niente accumulo tra run, niente dedup (i dati RNA non hanno duplicati).

**Robustezza**: due filtri in cascata sullo stream XML — `XMLCharFilter` rimuove byte XML non validi, `XMLTagFixer` corregge tag troncati nei file della fonte (BASE_GIURIDICA_NAZ → BASE_GIURIDICA_NAZIONALE, IMPORTO_NOMIN → IMPORTO_NOMINALE).

## CI

Il batch completo (114 file, 2017-2026, ~40 GB di XML) processa in ~3 ore su un runner self-hosted (Oracle Cloud, ARM64, 6GB RAM). Ogni file viene scritto subito su disco — picco RAM sotto 500 MB anche con 4 worker paralleli.

Per l'aggiornamento mensile si processano solo i mesi nuovi (1-3 file, ~3-8 minuti).

### Workflow `test`
Attivato su push/PR: installa il pacchetto, esegue i test. CI bloccante.

### Workflow `build`
Attivato su schedule (mensile) o manualmente. Processa i file RNA, scrive parquet, pusha a GCS, aggiorna MANIFEST.json.

## Manutenzione — aggiungere un campo

Lo schema è definito in **un solo posto**: `rna_aiuti/parser.py` (variabili `SCHEMA` e `FIELD_NAMES`).  
Se aggiungi un campo:
1. Aggiorna `SCHEMA` in `parser.py`
2. Aggiorna `dataset.yml` per la documentazione
3. Se il campo è parte della dedup key, aggiorna `DEDUP_KEY`

## Fonti

- **Dati originali**: [RNA — Registro Nazionale Aiuti di Stato](https://www.rna.gov.it/open-data) (MIMIT, CC BY 3.0)
- **Catalogo**: [dati.gov.it — MIMIT](https://dati.gov.it/opendata/organization/mimit)
- **Regolamento**: Trasparenza aiuti di Stato (L. 234/2012)

## Licenza

- **Dati**: CC BY 3.0 (MIMIT — Ministero delle Imprese e del Made in Italy)
- **Codice**: MIT
