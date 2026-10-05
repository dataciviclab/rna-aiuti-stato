"""Smoke test — pagine dashboard compilano senza errori di sintassi.

Pattern standard Lab (opere-pubbliche, dichiarazioni-italia, terzo-settore):
py_compile sulle pagine. Nessun import di streamlit, nessun PYTHONPATH.
"""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"


@pytest.mark.parametrize(
    "page",
    sorted(PAGES_DIR.glob("*.py")),
    ids=lambda p: p.stem,
)
def test_page_compiles(page: Path) -> None:
    """Ogni pagina deve compilarsi senza errori di sintassi."""
    py_compile.compile(str(page), doraise=True)
