#!/usr/bin/env python3
"""
Wrapper per toolkit.cli.app che configura DuckDB prima dell'esecuzione.

Monkey-patcha duckdb.connect() per impostare memory_limit e threads
su ogni nuova connessione, prevenendo OutOfMemory nei runner CI con
2GB di RAM (GitHub Actions free).

Usage:
  python3 scripts/run_toolkit.py run --config datasets/siope-entrate/dataset.yml --years "2021,2022,2023,2024,2025,2026"
"""
import duckdb
import sys

# ── DuckDB config per CI ─────────────────────────────────────────────────────
# GitHub Actions runners hanno ~2GB RAM. DuckDB di default cerca di usare tutta.
# Questi limiti prevengono OOM durante GROUP BY su milioni di righe.
_MEMORY_LIMIT = "1.5GB"
_THREADS = 2
_PRESERVE_ORDER = False

_original_connect = duckdb.connect


def _patched_connect(*args, **kwargs):
    con = _original_connect(*args, **kwargs)
    con.execute(f"SET memory_limit='{_MEMORY_LIMIT}'")
    con.execute(f"SET preserve_insertion_order={str(_PRESERVE_ORDER).lower()}")
    con.execute(f"SET threads={_THREADS}")
    return con


duckdb.connect = _patched_connect

# ── Chiama toolkit ───────────────────────────────────────────────────────────
# typer.Typer() legge sys.argv al momento della chiamata
from toolkit.cli.app import app  # noqa: E402

app()
