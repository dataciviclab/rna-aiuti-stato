"""Smoke test — verifica che tutte le pagine si importano senza errori."""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.smoke

PAGES = [
    "pages.01_Overview",
    "pages.02_Territorio",
    "pages.03_Policy",
    "pages.04_Cerca",
]


@pytest.mark.parametrize("module", PAGES)
def test_page_imports(module: str) -> None:
    """Ogni pagina deve importarsi senza errori."""
    importlib.import_module(module)
