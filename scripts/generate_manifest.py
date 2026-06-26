#!/usr/bin/env python3
"""Genera MANIFEST.json dal catalogo parquet.

Uso:
    python3 scripts/generate_manifest.py data/derived/rna/
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

GCS_PREFIX = "gs://dataciviclab-clean/rna-aiuti-stato/"


def generate_manifest(parquet_dir: str | Path) -> dict:
    parquet_dir = Path(parquet_dir)
    files = sorted(parquet_dir.glob("rna_*.parquet"))

    if not files:
        print("Nessun parquet trovato.")
        sys.exit(1)

    years = []
    file_info = {}
    total_rows = 0
    total_size = 0

    for pf in files:
        meta = pq.read_metadata(str(pf))
        n_rows = meta.num_rows
        size_mb = round(pf.stat().st_size / 1_000_000, 1)

        # Estrai anno dal nome
        year = int(pf.stem.replace("rna_", ""))
        years.append(year)
        file_info[pf.name] = {
            "rows": n_rows,
            "size_mb": size_mb,
            "gcs_uri": f"{GCS_PREFIX}{pf.name}",
            "months": None,  # si può calcolare da DuckDB se serve
        }
        total_rows += n_rows
        total_size += size_mb

    manifest = {
        "dataset": "rna_aiuti_stato",
        "description": "Registro Nazionale Aiuti di Stato — ogni aiuto pubblico concesso alle imprese italiane",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": "https://www.rna.gov.it/open-data",
        "license": "CC BY 3.0",
        "gcs_prefix": GCS_PREFIX,
        "years": sorted(years),
        "files": {k: file_info[k] for k in sorted(file_info)},
        "total_rows": total_rows,
        "total_size_mb": round(total_size, 1),
        "build_info": {
            "parser_version": "0.1.0",
            "schema_fields": 29,
            "dedup_key": "cor, id_componente, cod_strumento",
        },
    }

    return manifest


def main():
    if len(sys.argv) < 2:
        parquet_dir = "data/derived/rna"
    else:
        parquet_dir = sys.argv[1]

    manifest = generate_manifest(parquet_dir)

    out_path = Path("data/derived/MANIFEST.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest scritto: {out_path}")
    print(f"  Anni: {manifest['years']}")
    print(f"  Righe totali: {manifest['total_rows']:,}")
    print(f"  Dimensione: {manifest['total_size_mb']} MB")


if __name__ == "__main__":
    main()
