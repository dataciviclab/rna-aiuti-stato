"""Fonti dati per la dashboard RNA Aiuti di Stato.

Layer sottile che wrappa ``lab_connectors.duckdb.queries`` con
``@st.cache_data`` per Streamlit. Tutta la logica di risoluzione
path GCS e DuckDB sta in lab-connectors — qui solo la cache.

**Modalità locale**: se ``out/data/`` esiste (sviluppo locale), legge i
parquet dal filesystem invece che da GCS (via ``local_root`` di lab-connectors).
Gli anni vengono derivati dai parquet disponibili, non dal registry.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab_connectors.duckdb.queries import (
    count_rows as _count_rows,
    load_clean as _load_clean,
    load_mart_all_years as _load_mart_all_years,
    load_mart_table as _load_mart_table,
    query_clean as _query_clean,
)
from lab_connectors.formatters import fmt_eur, fmt_num, fmt_pct
from lab_connectors.registry import load_registry

# ── Detection modalità locale/GCS ───────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
_OUT_DATA = _REPO_ROOT / "out" / "data"
_LOCAL_MODE = _OUT_DATA.is_dir()

# Quando locale: local_root è la root per il toolkit (out/data/),
# quando GCS: None (comportamento default di lab-connectors).
LOCAL_ROOT: str | None = str(_OUT_DATA) if _LOCAL_MODE else None


def _detect_years_from_files(slug: str, layer: str = "mart") -> list[int]:
    """Deriva gli anni disponibili dai parquet su disco (modalità locale)."""
    base = _OUT_DATA / layer / slug
    if not base.is_dir():
        return []
    years = []
    for d in sorted(base.iterdir()):
        if d.is_dir() and d.name.isdigit():
            # Verifica che ci sia almeno un .parquet
            if any(d.glob("*.parquet")):
                years.append(int(d.name))
    return years


def _detect_misure_year_from_files() -> int | None:
    """Trova l'anno del run misure (dataset cumulativo)."""
    base = _OUT_DATA / "mart" / "rna_misure"
    if not base.is_dir():
        return None
    years = sorted(d.name for d in base.iterdir() if d.is_dir() and d.name.isdigit())
    return int(years[-1]) if years else None


# ── Costanti dominio ────────────────────────────────────────────────────────

SLUG = "rna_aiuti_stato"
SLUG_MISURE = "rna_misure"

_registry = load_registry(_REPO_ROOT / "registry" / "registry.json")
_ds = next((d for d in _registry.datasets if d.slug == SLUG), None)
if _ds and _ds.period:
    _p = _ds.period
    _start = getattr(_p, "start", None) or (_p.get("start") if isinstance(_p, dict) else None)
    _end = getattr(_p, "end", None) or (_p.get("end") if isinstance(_p, dict) else None)
    _YEARS_REG = list(range(int(_start), int(_end) + 1)) if _start and _end else []
else:
    _YEARS_REG = []

# YEARS: se locale → dai file; altrimenti dal registry
YEARS = _detect_years_from_files(SLUG) if _LOCAL_MODE else _YEARS_REG

# Mart tables disponibili (confermate in dataset.yml + GCS)
MART_REGIONE = "mart_aiuti_per_regione"
MART_PROCEDIMENTO = "mart_aiuti_per_procedimento"
MART_TOP = "mart_aiuti_top_beneficiari"
MART_TIPO_BENEF = "mart_aiuti_tipo_beneficiario"
MART_SETTORE = "mart_aiuti_settore_regione"
MART_OBIETTIVO = "mart_aiuti_per_obiettivo"
MART_STRUMENTO = "mart_aiuti_per_strumento"
MART_MISURA = "mart_aiuti_per_misura"

# Mart tables rna_misure
MART_TOP_MISURE = "mart_top_misure"

# Anno del run misure: cumulativo, derivato dal file system o registry
if _LOCAL_MODE:
    MISURE_YEAR = _detect_misure_year_from_files()
else:
    _ds_misure = next((d for d in _registry.datasets if d.slug == SLUG_MISURE), None)
    if _ds_misure and _ds_misure.period:
        _pm = _ds_misure.period
        _end_m = _pm.get("end") if isinstance(_pm, dict) else getattr(_pm, "end", None)
        MISURE_YEAR = int(_end_m) if _end_m else None
    else:
        MISURE_YEAR = None


# ── Cached wrappers ─────────────────────────────────────────────────────────


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart(table: str, year: int, slug: str = SLUG):
    """Carica un singolo mart table (cached 1h). Locale o GCS."""
    return _load_mart_table(slug, table, year, local_root=LOCAL_ROOT)


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart_years(table: str, years: tuple[int, ...] = tuple(YEARS), slug: str = SLUG):
    """Carica un mart table per tutti gli anni (cached 1h)."""
    return _load_mart_all_years(slug, table, list(years), local_root=LOCAL_ROOT)


@st.cache_data(ttl=3600, show_spinner=False)
def load_clean_data(years: tuple[int, ...] = tuple(YEARS)):
    """Carica il clean layer per tutti gli anni (cached 1h)."""
    return _load_clean(SLUG, list(years), local_root=LOCAL_ROOT)


@st.cache_data(ttl=3600, show_spinner=False)
def run_sql(sql: str, years: tuple[int, ...] = tuple(YEARS)):
    """Esegue SQL sul clean layer (cached 1h)."""
    return _query_clean(SLUG, sql, list(years), local_root=LOCAL_ROOT)


@st.cache_data(ttl=3600, show_spinner=False)
def get_row_count(year: int):
    """Conta righe clean per un anno (cached 1h)."""
    return _count_rows(SLUG, year, local_root=LOCAL_ROOT)
