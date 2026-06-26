# rna_aiuti — parsing del Registro Nazionale Aiuti di Stato
from __future__ import annotations

from rna_aiuti.parser import (
    # Core
    flatten_aiuto,
    extract_aiuto_base,
    extract_componente,
    extract_strumento,
    # Schema
    SCHEMA,
    FIELD_NAMES,
    DEDUP_KEY,
    # I/O
    write_partition,
    extract_streaming,
    summary,
    # Stream filter
    XMLCharFilter,
    XMLTagFixer,
)

__all__ = [
    "flatten_aiuto",
    "extract_aiuto_base",
    "extract_componente",
    "extract_strumento",
    "SCHEMA",
    "FIELD_NAMES",
    "DEDUP_KEY",
    "write_partition",
    "extract_streaming",
    "summary",
    "XMLCharFilter",
    "XMLTagFixer",
]
