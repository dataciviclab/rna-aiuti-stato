#!/usr/bin/env python3
"""Estrazione RNA — da XML a Parquet, partizionato per anno.

Uso:
    # Singolo mese → appende al parquet dell'anno
    python3 scripts/extract.py data/raw/OpenData_Aiuti_2017_01.xml

    # Batch su tutti i mesi presenti in data/raw/
    python3 scripts/extract.py --batch data/raw/

    # Mostra riepilogo del catalogo parquet
    python3 scripts/extract.py --summary data/derived/rna/

Non carica mai l'intero file XML in memoria: usa ``iterparse``
in streaming per processare un <AIUTO> alla volta.
"""

from __future__ import annotations

import argparse
import glob
import logging
import re
import sys
import time
import typing
from collections import defaultdict
from pathlib import Path

import lxml.etree as ET
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rna_aiuti.parser import flatten_aiuto

logger = logging.getLogger("rna.extract")

NS = "{http://www.rna.it/RNA_aiuto/schema}"
TAG_AIUTO = f"{NS}AIUTO"

# Schema con anno/mese aggiunti per partizionamento
SCHEMA = pa.schema([
    # AIUTO (17 campi)
    pa.field("data_concessione", pa.string()),
    pa.field("car", pa.string()),
    pa.field("cor", pa.string()),
    pa.field("denominazione_beneficiario", pa.string()),
    pa.field("codice_fiscale_beneficiario", pa.string()),
    pa.field("tipo_beneficiario", pa.string()),
    pa.field("regione_beneficiario", pa.string()),
    pa.field("soggetto_concedente", pa.string()),
    pa.field("titolo_misura", pa.string()),
    pa.field("des_tipo_misura", pa.string()),
    pa.field("titolo_progetto", pa.string()),
    pa.field("descrizione_progetto", pa.string()),
    pa.field("cup", pa.string()),
    pa.field("atto_concessione", pa.string()),
    pa.field("base_giuridica_nazionale", pa.string()),
    pa.field("identificativo_ufficio", pa.string()),
    pa.field("link_trasparenza_nazionale", pa.string()),
    # COMPONENTE (8 campi)
    pa.field("id_componente", pa.string()),
    pa.field("procedimento", pa.string()),
    pa.field("cod_procedimento", pa.string()),
    pa.field("regolamento_ue", pa.string()),
    pa.field("cod_regolamento", pa.string()),
    pa.field("obiettivo", pa.string()),
    pa.field("cod_obiettivo", pa.string()),
    pa.field("settore_attivita", pa.string()),
    # STRUMENTO (4 campi)
    pa.field("cod_strumento", pa.string()),
    pa.field("strumento", pa.string()),
    pa.field("elemento_aiuto", pa.float64()),
    pa.field("importo_nominale", pa.float64()),
    # Partizione (2 campi)
    pa.field("anno", pa.int32()),
    pa.field("mese", pa.int32()),
])

FIELD_NAMES = [f.name for f in SCHEMA]


def _parse_year_month(data_concessione: str) -> tuple[int, int]:
    """Estrae anno e mese da una data concessione."""
    if not data_concessione:
        return 0, 0
    parts = data_concessione.split("-")
    if len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    return 0, 0


def extract_streaming(
    source: str | Path | typing.BinaryIO,
    page_size: int = 5000,
) -> dict[int, list[dict]]:
    """Processa RNA XML in streaming, da file o da file-like object (HTTP).

    Args:
        source: Path del file XML **oppure** file-like object binario
                (es. ``requests.get(url, stream=True).raw``).
        page_size: Righe intermedie per log.

    Returns:
        Dict {anno: [righe]}.
    """
    t0 = time.time()
    total_aiuti = 0

    rows_by_year: dict[int, list[dict]] = defaultdict(list)

    if isinstance(source, (str, Path)):
        # Path locale
        context = ET.iterparse(str(source), events=("end",), tag=TAG_AIUTO)
    else:
        # File-like object (HTTP streaming)
        context = ET.iterparse(source, events=("end",), tag=TAG_AIUTO)

    for _event, elem in context:
        total_aiuti += 1
        flat_rows = flatten_aiuto(elem)

        for row in flat_rows:
            anno, mese = _parse_year_month(row.get("data_concessione", ""))
            row["anno"] = anno
            row["mese"] = mese
            rows_by_year[anno].append(row)

        # Libera memoria
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

        if total_aiuti % page_size == 0:
            logger.info("  %d aiuti processati ...", total_aiuti)

    t1 = time.time()
    elapsed = t1 - t0
    total_rows = sum(len(v) for v in rows_by_year.values())

    logger.info("  %d aiuti → %d righe in %.1f sec (%.0f aiuti/sec)",
                total_aiuti, total_rows, elapsed, total_aiuti / elapsed if elapsed else 0)

    return dict(rows_by_year)


def _to_table(rows: list[dict]) -> pa.Table:
    """Converte una lista di dict in tabella PyArrow."""
    batch: dict[str, list] = {f: [] for f in FIELD_NAMES}
    for row in rows:
        for field in FIELD_NAMES:
            batch[field].append(row.get(field))
    return pa.Table.from_pydict(batch, schema=SCHEMA)


def write_partition(rows: list[dict], base_dir: str | Path, year: int):
    """Scrive o appende righe al parquet annuale."""
    base_dir = Path(base_dir)
    out_path = base_dir / f"rna_{year}.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    new_table = _to_table(rows)

    if out_path.exists():
        old_table = pq.read_table(str(out_path))
        n_old = old_table.num_rows
        combined = pa.concat_tables([old_table, new_table])
        # Dedup: ultima riga per (cor, id_componente, cod_strumento) vince
        # Si può fare in DuckDB al consumo; per ora teniamo tutto
        n_new = new_table.num_rows
        pq.write_table(combined, str(out_path), compression="zstd")
        logger.info("  → %s: %d righe (old %d + new %d)", out_path.name, n_old + n_new, n_old, n_new)
    else:
        n = new_table.num_rows
        pq.write_table(new_table, str(out_path), compression="zstd")
        logger.info("  → %s: %d righe (nuovo)", out_path.name, n)

    return out_path


def process_file(xml_path: str | Path, out_dir: str | Path, page_size: int = 5000) -> dict:
    """Processa un singolo file XML: estrae e scrive partizione annuale."""
    xml_path = Path(xml_path)
    out_dir = Path(out_dir)
    logger.info("Processing: %s", xml_path.name)

    rows_by_year = extract_streaming(xml_path, page_size=page_size)

    total_rows = 0
    for year, rows in sorted(rows_by_year.items()):
        if year == 0:
            logger.warning("  ⚠ %d righe senza anno valido, saltate", len(rows))
            continue
        write_partition(rows, out_dir, year)
        total_rows += len(rows)

    return {
        "file": xml_path.name,
        "anni": sorted(rows_by_year.keys()),
        "righe": total_rows,
    }


def summary(out_dir: str | Path):
    """Mostra riepilogo di tutti i parquet annuali."""
    out_dir = Path(out_dir)
    parquet_files = sorted(out_dir.glob("rna_*.parquet"))

    if not parquet_files:
        logger.info("Nessun parquet trovato in %s", out_dir)
        return

    logger.info("")
    logger.info("=== CATALOGO RNA PARQUET ===")
    logger.info("%-15s %10s %12s", "File", "Righe", "Dimensione")
    logger.info("-" * 40)

    total_rows = 0
    total_size = 0
    for pf in parquet_files:
        table = pq.read_metadata(str(pf))
        n_rows = table.num_rows
        size_mb = pf.stat().st_size / 1_000_000
        total_rows += n_rows
        total_size += size_mb
        logger.info("%-15s %10d %10.1f MB", pf.stem, n_rows, size_mb)

    logger.info("-" * 40)
    logger.info("%-15s %10d %10.1f MB", "TOTALE", total_rows, total_size)


def batch_process(raw_dir: str | Path, out_dir: str | Path):
    """Processa tutti i file XML in una directory."""
    raw_dir = Path(raw_dir)
    xml_files = sorted(raw_dir.glob("OpenData_Aiuti_*.xml"))
    logger.info("Batch: %d file XML trovati in %s", len(xml_files), raw_dir)

    total_righe = 0
    total_tempo = 0
    for xml_file in xml_files:
        t0 = time.time()
        try:
            process_file(xml_file, out_dir)
            elapsed = time.time() - t0
            total_tempo += elapsed
            total_righe += 0  # lo process_file logga già
        except Exception as e:
            logger.error("  ❌ %s: %s", xml_file.name, e)

    logger.info("")
    logger.info("Batch completato: %d file in %.1f minuti", len(xml_files), total_tempo / 60)


def main():
    parser = argparse.ArgumentParser(description="RNA XML → Parquet partizionato per anno")
    parser.add_argument("target", type=str, nargs="?", default=None,
                        help="File XML o directory (con --batch)")
    parser.add_argument("-o", "--out", type=str, default="data/derived/rna",
                        help="Directory output parquet (default: data/derived/rna)")
    parser.add_argument("--page-size", type=int, default=5000,
                        help="Righe per log intermedio (default: 5000)")
    parser.add_argument("--batch", action="store_true",
                        help="Processa tutti i file XML in una directory")
    parser.add_argument("--summary", action="store_true",
                        help="Mostra riepilogo dei parquet nella directory output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.summary:
        summary(args.target if args.target else args.out)
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
        process_file(target, args.out, page_size=args.page_size)
        return

    # Nessun argomento: mostra usage
    parser.print_help()


if __name__ == "__main__":
    main()
