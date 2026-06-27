# rna_aiuti — parsing del Registro Nazionale Aiuti di Stato
from __future__ import annotations

from rna_aiuti.parser import (
    # Core Aiuti
    flatten_aiuto,
    extract_aiuto_base,
    extract_componente,
    extract_strumento,
    # Core Misure
    extract_misura,
    # Schema Aiuti
    SCHEMA,
    FIELD_NAMES,
    DEDUP_KEY,
    # Schema Misure
    MISURA_SCHEMA,
    MISURA_FIELD_NAMES,
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
    "extract_misura",
    "SCHEMA",
    "FIELD_NAMES",
    "DEDUP_KEY",
    "MISURA_SCHEMA",
    "MISURA_FIELD_NAMES",
    "write_partition",
    "extract_streaming",
    "summary",
    "XMLCharFilter",
    "XMLTagFixer",
]
