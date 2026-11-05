"""Test degli URL della fonte RNA.

Regressione: dal 2026 la fonte è servita dal portale Incentivi Italia
(www.incentivitalia.gov.it). Il vecchio www.rna.gov.it reindirizza lì
restituendo HTML, non XML — se questi URL tornano al vecchio host la
pipeline scarica pagine HTML e produce parquet vuoti/corrotti.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

NEW_AIUTI_PREFIX = "https://www.incentivitalia.gov.it/open-data/aiuti/"
NEW_MISURA_PREFIX = "https://www.incentivitalia.gov.it/open-data/misura/"
OLD_HOST = "www.rna.gov.it"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


full_batch = _load_module("rna_full_batch", "full_batch.py")


@pytest.mark.contract
def test_aiuti_urls_point_to_new_portal():
    """RNA_URLS usano il nuovo host e non il vecchio rna.gov.it."""
    assert full_batch.RNA_URLS, "RNA_URLS non deve essere vuoto"
    for url in full_batch.RNA_URLS:
        assert url.startswith(NEW_AIUTI_PREFIX), url
        assert OLD_HOST not in url, url


@pytest.mark.contract
def test_misure_urls_point_to_new_portal():
    """MISURA_URLS usano il nuovo host e non il vecchio rna.gov.it."""
    assert full_batch.MISURA_URLS, "MISURA_URLS non deve essere vuoto"
    for url in full_batch.MISURA_URLS:
        assert url.startswith(NEW_MISURA_PREFIX), url
        assert OLD_HOST not in url, url


@pytest.mark.contract
def test_url_filename_pattern():
    """I nomi file restano OpenData_{Aiuti,Misura}_YYYY_MM.xml."""
    for url in full_batch.RNA_URLS:
        name = Path(url).name
        assert name.startswith("OpenData_Aiuti_") and name.endswith(".xml"), url
    for url in full_batch.MISURA_URLS:
        name = Path(url).name
        assert name.startswith("OpenData_Misura_") and name.endswith(".xml"), url


@pytest.mark.contract
def test_misure_urls_cover_next_year():
    """Le Misure hanno DATA_INIZIO futura: si genera fino all'anno successivo.

    Regressione: il cutoff al mese corrente escludeva i file Misura con start
    futuro (es. 2027_01, 2027_12) e, siccome `_run_misure` ricostruisce
    `misure.parquet` da zero, le righe già presenti andavano perse.
    """
    now = datetime.now(timezone.utc)
    years = {int(Path(u).name.split("_")[2]) for u in full_batch.MISURA_URLS}
    assert max(years) >= now.year + 1, (
        f"max anno Misure = {max(years)}, atteso >= {now.year + 1}"
    )
    # tutti i 12 mesi dell'anno successivo devono essere generati
    next_year_months = {
        int(Path(u).name.split("_")[3].split(".")[0])
        for u in full_batch.MISURA_URLS
        if int(Path(u).name.split("_")[2]) == now.year + 1
    }
    assert next_year_months == set(range(1, 13)), next_year_months
