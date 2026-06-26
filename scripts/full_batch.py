#!/usr/bin/env python3
"""Batch parallelo RNA — download streaming + parse, zero storage raw.

Scarica ogni file XML in HTTP streaming e lo processa ``iterparse``
al volo, senza mai scriverlo su disco. I worker paralleli saturano
la banda di rete, non la CPU.

Uso:
    # Periodo specifico (default 2 worker)
    python3 scripts/full_batch.py --from 2023 --to 2025

    # Full (tutti i 133 file)
    python3 scripts/full_batch.py --full

    # Summary
    python3 scripts/full_batch.py --summary

    # Parallelismo
    python3 scripts/full_batch.py --full --workers 4
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import lxml.etree as ET
import urllib.request

from rna_aiuti.parser import (
    flatten_aiuto,
    parse_year_month,
    write_partition,
    XMLCharFilter,
    XMLTagFixer,
    summary as _summary,
)

logger = logging.getLogger("rna.batch")

NS = "{http://www.rna.it/RNA_aiuto/schema}"
TAG_AIUTO = f"{NS}AIUTO"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
MAX_RETRIES = 5
RETRY_DELAY = 10  # secondi

# Tutti gli URL RNA (2017-01 → 2026-06)
RNA_URLS = [
    f"https://www.rna.gov.it/sites/rna.mise.gov.it/files/opendata/OpenData_Aiuti_{y:04d}_{m:02d}.xml"
    for y in range(2017, 2027)
    for m in range(1, 13)
    if not (y == 2026 and m > 6)
]


def _download_with_retry(url: str) -> object:
    """Download con retry e backoff. Restituisce file-like object (XML filtrato)."""
    import urllib.error

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/xml, text/xml, */*",
            })
            resp = urllib.request.urlopen(req, timeout=600)
            return XMLCharFilter(resp)
        except (urllib.error.URLError, OSError) as e:
            last_error = e
            fname = url.split("/")[-1]
            logger.warning("  ⚠ %s tentativo %d/%d: %s", fname, attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    raise last_error  # type: ignore


def process_url(url: str) -> dict:
    """Scarica in streaming e parse un file RNA.

    Restituisce {anno: [righe]}.
    """
    fname = url.split("/")[-1]
    logger.info("  ↓ %s", fname)
    t0 = time.time()

    resp = _download_with_retry(url)
    # Filtra tag troncati noti (BASE_GIURIDICA_NAZ, IMPORTO_NOMIN, …)
    resp = XMLTagFixer(resp)

    rows_by_year: dict[int, list] = {}
    total_aiuti = 0

    context = ET.iterparse(resp, events=("end",), tag=TAG_AIUTO,
                           recover=True)
    for _event, elem in context:
        total_aiuti += 1
        flat_rows = flatten_aiuto(elem)
        for row in flat_rows:
            anno, mese = parse_year_month(row.get("data_concessione", ""))
            row["anno"] = anno
            row["mese"] = mese
            rows_by_year.setdefault(anno, []).append(row)

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    elapsed = time.time() - t0
    total_rows = sum(len(v) for v in rows_by_year.values())
    logger.info("  ✓ %s: %d aiuti → %d righe in %.1f sec",
                fname, total_aiuti, total_rows, elapsed)

    return rows_by_year


def build_url_list(from_year: int, to_year: int) -> list[str]:
    """Filtra URL per intervallo anni."""
    def _year(url: str) -> int:
        fname = url.split("/")[-1].replace(".xml", "")
        return int(fname.split("_")[2])
    return [u for u in RNA_URLS if from_year <= _year(u) <= to_year]


def main():
    parser = argparse.ArgumentParser(description="RNA batch parallelo")
    parser.add_argument("--from", dest="from_year", type=int, default=2017,
                        help="Anno iniziale (default: 2017)")
    parser.add_argument("--to", dest="to_year", type=int, default=2026,
                        help="Anno finale (default: 2026)")
    parser.add_argument("--workers", type=int, default=2,
                        help="Worker paralleli (default: 2, VM 6GB RAM)")
    parser.add_argument("--full", action="store_true",
                        help="Processa tutti i 133 file (override --from/--to)")
    parser.add_argument("-o", "--out", type=str, default="data/derived/rna",
                        help="Directory output parquet (default: data/derived/rna)")
    parser.add_argument("--summary", action="store_true",
                        help="Mostra riepilogo dei parquet nella directory output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    out_dir = Path(args.out)

    # Se --summary, mostra e basta
    if args.summary:
        _summary(out_dir)
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    # Seleziona URL
    if args.full:
        urls = RNA_URLS
        label = "TUTTI 133 file"
    else:
        urls = build_url_list(args.from_year, args.to_year)
        label = f"{len(urls)} file ({args.from_year}-{args.to_year})"

    logger.info("RNA batch — %s · %d worker", label, args.workers)
    logger.info("Output: %s", out_dir)
    logger.info("")

    t_start = time.time()
    years_data: dict[int, list] = {}
    done = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futmap = {executor.submit(process_url, u): u for u in urls}

        for fut in as_completed(futmap):
            url = futmap[fut]
            fname = url.split("/")[-1]
            try:
                result = fut.result()
                for y, rows in result.items():
                    years_data.setdefault(y, []).extend(rows)
                done += 1
            except Exception as e:
                logger.error("  ✗ %s: %s", fname, e)
                failed += 1

    # Scrive partizioni annuali (sovrascrive con dedup)
    logger.info("")
    logger.info("Scrittura partizioni per anno ...")
    total_rows = 0
    for year in sorted(years_data):
        rows = years_data[year]
        if not rows or year == 0:
            continue
        write_partition(rows, out_dir, year, mode="overwrite", dedup=True)
        total_rows += len(rows)

    elapsed = time.time() - t_start
    logger.info("")
    logger.info("=== COMPLETATO ===")
    logger.info("  File:   %d OK, %d falliti", done, failed)
    logger.info("  Righe:  %d", total_rows)
    logger.info("  Tempo:  %.1f min", elapsed / 60)

    # Summary
    total_mb = sum(f.stat().st_size for f in out_dir.glob("rna_*.parquet")) / 1_000_000
    logger.info("  Output: %s (%.0f MB)", out_dir, total_mb)


if __name__ == "__main__":
    main()
