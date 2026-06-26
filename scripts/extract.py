#!/usr/bin/env python3
"""Estrazione RNA — da XML a Parquet, partizionato per anno (CLI thin).

Uso:
    # Singolo mese — processa e appende al parquet dell'anno
    python3 scripts/extract.py data/raw/OpenData_Aiuti_2017_01.xml

    # Batch su tutti i mesi presenti in data/raw/
    python3 scripts/extract.py --batch data/raw/

    # Mostra riepilogo del catalogo parquet
    python3 scripts/extract.py --summary data/derived/rna/

La logica di business è in ``rna_aiuti.parser``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rna_aiuti.parser import extract_streaming, write_partition, summary as _summary

logger = logging.getLogger("rna.extract")


def batch_process(raw_dir: str | Path, out_dir: str | Path):
    """Processa tutti i file XML in una directory."""
    raw_dir = Path(raw_dir)
    xml_files = sorted(raw_dir.glob("OpenData_Aiuti_*.xml"))
    logger.info("Batch: %d file XML trovati in %s", len(xml_files), raw_dir)

    for xml_file in xml_files:
        try:
            _process_one(xml_file, out_dir)
        except Exception as e:
            logger.error("  ❌ %s: %s", xml_file.name, e)


def _process_one(xml_path: Path, out_dir: Path):
    """Processa un singolo file XML."""
    logger.info("Processing: %s", xml_path.name)
    rows_by_year = extract_streaming(xml_path)

    for year, rows in sorted(rows_by_year.items()):
        if year == 0:
            logger.warning("  ⚠ %d righe senza anno valido, saltate", len(rows))
            continue
        write_partition(rows, out_dir, year, mode="append")


def main():
    parser = argparse.ArgumentParser(description="RNA XML → Parquet partizionato per anno")
    parser.add_argument("target", type=str, nargs="?", default=None,
                        help="File XML o directory (con --batch)")
    parser.add_argument("-o", "--out", type=str, default="data/derived/rna",
                        help="Directory output parquet (default: data/derived/rna)")
    parser.add_argument("--batch", action="store_true",
                        help="Processa tutti i file XML in una directory")
    parser.add_argument("--summary", action="store_true",
                        help="Mostra riepilogo dei parquet nella directory output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.summary:
        _summary(args.target if args.target else args.out)
        return

    if args.batch:
        if not args.target:
            logger.error("Serve una directory con --batch")
            sys.exit(1)
        batch_process(args.target, args.out)
        return

    if args.target:
        target = Path(args.target)
        if not target.exists():
            logger.error("File non trovato: %s", target)
            sys.exit(1)
        _process_one(target, Path(args.out))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
