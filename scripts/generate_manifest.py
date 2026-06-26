#!/usr/bin/env python3
"""Genera manifest annuali + index dai parquet RNA.

Uso:
    python3 scripts/generate_manifest.py

Produce:
    data/derived/manifests/rna_YYYY.json   — per ogni anno con parquet
    data/derived/manifests/rna_index.json   — sommario globale
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

GCS_PREFIX = "gs://dataciviclab-clean/rna-aiuti-stato/"
PARQUET_DIR = Path("data/derived/rna")
MANIFEST_DIR = Path("data/derived/manifests")


def _source_months_for_year(year: int) -> int:
    """Quanti mesi la fonte RNA ha pubblicato per quest'anno."""
    if year < 2017 or year > 2026:
        return 0
    if year == 2026:
        return 6  # fermo a giugno 2026
    return 12


def build_year_manifest(parquet_path: Path) -> dict:
    """Costruisce il manifest per un singolo anno."""
    year = int(parquet_path.stem.replace("rna_", ""))
    meta = pq.read_metadata(str(parquet_path))

    # Legge i mesi distinti presenti nel parquet (solo valori 1-12)
    tbl = pq.read_table(str(parquet_path), columns=["mese"])
    months = sorted(set(m for m in tbl.column("mese").to_pylist() if 1 <= m <= 12))

    size_mb = round(parquet_path.stat().st_size / 1_000_000, 1)
    source_months = _source_months_for_year(year)

    return {
        "year": year,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "months": months,
        "source_available_months": source_months,
        "completeness": min(1.0, round(len(months) / source_months, 2)) if source_months else 0.0,
        "rows": meta.num_rows,
        "size_mb": size_mb,
        "gcs_uri": f"{GCS_PREFIX}{parquet_path.name}",
        "parquet": parquet_path.name,
    }


def build_index(year_manifests: list[dict]) -> dict:
    """Aggrega i manifest annuali in un indice globale."""
    total_rows = sum(m["rows"] for m in year_manifests)
    total_size = sum(m["size_mb"] for m in year_manifests)

    return {
        "dataset": "rna_aiuti_stato",
        "description": "Registro Nazionale Aiuti di Stato",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": "https://www.rna.gov.it/open-data",
        "license": "CC BY 4.0",
        "gcs_prefix": GCS_PREFIX,
        "years": sorted([m["year"] for m in year_manifests]),
        "year_manifests": {
            m["year"]: {
                "months": m["months"],
                "completeness": m["completeness"],
                "rows": m["rows"],
                "size_mb": m["size_mb"],
                "gcs_uri": m["gcs_uri"],
                "manifest_uri": f"manifests/rna_{m['year']}.json",
            }
            for m in year_manifests
        },
        "total_rows": total_rows,
        "total_size_mb": round(total_size, 1),
        "build_info": {
            "parser_version": "0.1.0",
            "schema_fields": 31,
        },
    }


def main():
    parquet_dir = PARQUET_DIR
    manifest_dir = MANIFEST_DIR

    if len(sys.argv) > 1:
        parquet_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        manifest_dir = Path(sys.argv[2])

    parquet_files = sorted(parquet_dir.glob("rna_*.parquet"))
    if not parquet_files:
        print("Nessun parquet trovato.")
        sys.exit(1)

    manifest_dir.mkdir(parents=True, exist_ok=True)

    year_manifests = []
    for pf in parquet_files:
        year = int(pf.stem.replace("rna_", ""))
        manifest = build_year_manifest(pf)
        year_manifests.append(manifest)

        # Scrive manifest annuale
        out_path = manifest_dir / f"rna_{year}.json"
        out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"  {out_path.name}: {manifest['rows']:,} righe, {manifest['months']} mesi, "
              f"completeness {manifest['completeness']}")

    # Scrive indice globale
    index = build_index(year_manifests)
    index_path = manifest_dir / "rna_index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"\n  {index_path.name}: {len(index['years'])} anni, "
          f"{index['total_rows']:,} righe totali, {index['total_size_mb']} MB")


if __name__ == "__main__":
    main()
