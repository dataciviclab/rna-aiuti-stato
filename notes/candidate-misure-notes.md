# Note — RNA Misure

## Note editoriali

- Le Misure definiscono i regimi di aiuto: ogni legge/decreto che autorizza aiuti di Stato
- Collegabili agli Aiuti via `car` (codice misura)
- Dati storici dal 1994 al 2023

## Note tecniche

- **Fonte**: XML del Registro Nazionale Aiuti di Stato (MIMIT)
- **Pipeline**: `rna-aiuti-stato/scripts/full_batch.py --misure`
- **GCS**: `gs://dataciviclab-clean/rna-aiuti-stato/misure/misure.parquet`
- **Deploy su GCS**: tramite CI di dataset-incubator (post-merge)
- **Forma**: unico parquet cumulativo (non partizionato per anno)

## Aggiornamento 2026-08-01 (standard v1)

- Mart flat passthrough rimossa; 3 mart analitiche serie (per_tipo, attive,
  top) — rispondono a D11 discussion #405
- PK clean = car + data_inizio_misura: car NON unico (stessa misura con più
  finestre di validità, es. car 1924: 2007-2021 e 2015-2030). Verificato:
  1 gruppo duplicato su car, 0 su car+inizio
- required_columns completato: mancavano importo_prestiti_garantiti e
  importo_aiuto_ad_hoc (le 2 metriche)
- Numeri chiave: regimi 177 mld, ad hoc 103 mld, Garanzia SupportItalia
  23 mld (COVID); 35 misure istituite nel 2020 ancora attive
- NOTA: importo = plafond misura, non erogato (join con rna_aiuti_stato via car)
