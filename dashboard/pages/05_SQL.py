"""Query SQL — Interroga direttamente i dati RNA Aiuti di Stato."""

from pathlib import Path

from lab_connectors.duckdb.sql_page import render_sql_query
from lab_connectors.registry import load_registry

registry = load_registry(Path(__file__).parent.parent.parent / "registry" / "registry.json")

render_sql_query(
    registry=registry,
    prefix="",
    default_slug="rna_aiuti_stato",
    title="🧪 Query SQL",
    description=(
        "Interroga direttamente i dati del Registro Nazionale Aiuti di Stato. "
        "Usa ``clean_input`` come nome della tabella virtuale."
    ),
)
