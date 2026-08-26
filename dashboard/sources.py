"""Fonti dati per la dashboard RNA Aiuti di Stato.

Layer sottile che wrappa ``lab_connectors.duckdb.queries`` con
``@st.cache_data`` per Streamlit. Tutta la logica di risoluzione
path GCS e DuckDB sta in lab-connectors — qui solo la cache.
"""

from __future__ import annotations

import streamlit as st

from lab_connectors.duckdb.queries import (
    count_rows as _count_rows,
    load_clean as _load_clean,
    load_mart_all_years as _load_mart_all_years,
    load_mart_table as _load_mart_table,
    query_clean as _query_clean,
)

# ── Costanti dominio ────────────────────────────────────────────────────────

SLUG = "rna_aiuti_stato"
SLUG_MISURE = "rna_misure"
YEARS = list(range(2017, 2026))

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


# ── Formattazione ───────────────────────────────────────────────────────────


def fmt_eur(value: float) -> str:
    """Formatta un valore in EUR leggibile."""
    if abs(value) >= 1_000_000_000:
        return f"€{value / 1_000_000_000:,.1f} mld"
    if abs(value) >= 1_000_000:
        return f"€{value / 1_000_000:,.1f} M"
    if abs(value) >= 1_000:
        return f"€{value / 1_000:,.0f} K"
    return f"€{value:,.0f}"


def fmt_num(value: int) -> str:
    """Formatta un numero con separatori."""
    return f"{value:,.0f}"


def fmt_pct(value: float) -> str:
    """Formatta una percentuale."""
    return f"{value:.1f}%"
