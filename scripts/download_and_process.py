#!/usr/bin/env python3
"""Download + Process + Cleanup — RNA Aiuti di Stato.

Scarica ogni file XML, lo processa in parquet, cancella l'XML.
Mantiene solo i parquet finali (~1-2 GB totali).
"""

import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger("rna.dl")

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/derived/rna")
CATALOG_URL = "https://storage.googleapis.com/dataciviclab-clean/catalog_inventory/catalog_inventory_latest.parquet"
EXTRACT_SCRIPT = Path("scripts/extract.py")
USER_AGENT = "Mozilla/5.0 (compatible; DataCivicLab/1.0)"


def get_urls() -> list[str]:
    """Recupera la lista di tutti gli URL RNA Aiuti."""
    logger.info("Fetching catalog inventory ...")
    df = pd.read_parquet(CATALOG_URL)
    rna = df[df["source_id"] == "mimit_rna"]
    aiuti = rna[rna["item_name"].str.contains("open-data-rna-aiuti", case=False, na=False)]
    urls = sorted(aiuti["distribution_url"].dropna().unique())
    logger.info("  Trovati %d file RNA Aiuti", len(urls))
    return urls


def download(url: str, dest: Path, timeout: int = 600) -> bool:
    """Scarica un file XML. Restituisce True se OK."""
    logger.info("  Download %s ...", dest.name)
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, stream=True)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                if chunk:
                    f.write(chunk)
        size_mb = dest.stat().st_size / 1_000_000
        logger.info("    ✓ %s (%.0f MB)", dest.name, size_mb)
        return True
    except Exception as e:
        logger.error("    ✗ %s: %s", dest.name, e)
        return False


def process(xml_path: Path) -> bool:
    """Processa un file XML in parquet."""
    logger.info("  Processing %s ...", xml_path.name)
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, str(EXTRACT_SCRIPT), str(xml_path), "-o", str(OUT_DIR)],
        capture_output=True, text=True, timeout=1200,
    )
    elapsed = time.time() - t0
    if result.returncode != 0:
        logger.error("    ✗ ERRORE: %s", result.stderr[:500])
        return False
    # Estrai numero righe dall'output
    for line in result.stdout.split("\n"):
        if "righe" in line and "→" in line:
            logger.info("    ✓ %s (%.1f sec)", xml_path.name, elapsed)
            break
    return True


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    urls = get_urls()

    # Filtra: salta file già processati
    already = set()
    for pf in OUT_DIR.glob("rna_*.parquet"):
        already.add(pf.stem.replace("rna_", ""))

    to_process = []
    for url in urls:
        fname = url.split("/")[-1]  # OpenData_Aiuti_YYYY_MM.xml
        year = fname.split("_")[2]
        # Check if this year-year-month is already in the parquet
    # Semplice: processa solo se il parquet annuale non esiste
    # (se esiste, l'extract fa append)

    # Per ora: processa TUTTI (l'extract gestisce append)
    # Ma teniamo traccia di quelli già fatti per log
    done = 0
    skipped = 0
    failed = 0

    for url in urls:
        fname = url.split("/")[-1]
        xml_path = RAW_DIR / fname

        # Skip se XML già scaricato e processato (il parquet esiste da un run precedente)
        # L'extract fa append, quindi se rilanciamo ripetiamo i dati
        # Per evitare duplicati, skippiamo se l'XML esiste già
        if xml_path.exists():
            logger.info("  ⏭ %s (già scaricato)", fname)
            skipped += 1
            # Potremmo processarlo lo stesso, ma per ora skip
            continue

        dl_ok = download(url, xml_path)
        if not dl_ok:
            failed += 1
            continue

        proc_ok = process(xml_path)
        if proc_ok:
            # Pulisce XML dopo processazione riuscita
            xml_path.unlink()
            done += 1
        else:
            failed += 1

        # Pausa leggera tra un file e l'altro per non stressare il server
        time.sleep(1)

    logger.info("")
    logger.info("=== COMPLETATO ===")
    logger.info("  Processati: %d", done)
    logger.info("  Saltati:    %d", skipped)
    logger.info("  Falliti:    %d", failed)

    # Summary finale
    logger.info("")
    result = subprocess.run(
        [sys.executable, str(EXTRACT_SCRIPT), "--summary", str(OUT_DIR)],
        capture_output=True, text=True,
    )
    for line in result.stdout.split("\n"):
        if line.strip():
            logger.info(line)


if __name__ == "__main__":
    main()
