"""Fonti dati per la dashboard RNA Aiuti di Stato.

Layer sottile che wrappa ``lab_connectors.duckdb.queries`` con
``@st.cache_data`` per Streamlit. Tutta la logica di risoluzione
path GCS e DuckDB sta in lab-connectors — qui solo la cache.
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

# ── Costanti dominio ────────────────────────────────────────────────────────

SLUG = "rna_aiuti_stato"
SLUG_MISURE = "rna_misure"

_registry = load_registry(Path(__file__).parent.parent / "registry" / "registry.json")
_ds = next((d for d in _registry.datasets if d.slug == SLUG), None)
if _ds and _ds.period:
    _p = _ds.period
    _start = getattr(_p, "start", None) or (_p.get("start") if isinstance(_p, dict) else None)
    _end = getattr(_p, "end", None) or (_p.get("end") if isinstance(_p, dict) else None)
    YEARS = list(range(int(_start), int(_end) + 1)) if _start and _end else []
else:
    YEARS = []

# Mart tables disponibili (confermate in dataset.yml + GCS)
MART_REGIONE = "mart_aiuti_per_regione"
MART_PROCEDIMENTO = "mart_aiuti_per_procedimento"
MART_TOP = "mart_aiuti_top_beneficiari"
MART_TIPO_BENEF = "mart_aiuti_tipo_beneficiario"
MART_SETTORE = "mart_aiuti_settore_regione"
MART_OBIETTIVO = "mart_aiuti_per_obiettivo"
MART_STRUMENTO = "mart_aiuti_per_strumento"

# Mart tables rna_misure
MART_TOP_MISURE = "mart_top_misure"


# ── Cached wrappers ─────────────────────────────────────────────────────────


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart(table: str, year: int, slug: str = SLUG):
    """Carica un singolo mart table da GCS (cached 1h)."""
    return _load_mart_table(slug, table, year)


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart_years(table: str, years: tuple[int, ...] = tuple(YEARS), slug: str = SLUG):
    """Carica un mart table per tutti gli anni (cached 1h)."""
    return _load_mart_all_years(slug, table, list(years))


@st.cache_data(ttl=3600, show_spinner=False)
def load_clean_data(years: tuple[int, ...] = tuple(YEARS)):
    """Carica il clean layer per tutti gli anni (cached 1h)."""
    return _load_clean(SLUG, list(years))


@st.cache_data(ttl=3600, show_spinner=False)
def run_sql(sql: str, years: tuple[int, ...] = tuple(YEARS)):
    """Esegue SQL sul clean layer (cached 1h)."""
    return _query_clean(SLUG, sql, list(years))


@st.cache_data(ttl=3600, show_spinner=False)
def get_row_count(year: int):
    """Conta righe clean per un anno (cached 1h)."""
    return _count_rows(SLUG, year)
