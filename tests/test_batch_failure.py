"""Guardrail: una run con download falliti non deve risultare "verde".

Regressione: `except Exception: failed += 1` non bloccava il job → un HTTP 500
sui file grossi (es. 2023_01, 2024_01, 2025_01) produceva una run verde con
parquet privi di quei mesi, perché ogni run ricostruisce gli anni da zero.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


full_batch = _load_module("rna_full_batch_guard", "full_batch.py")


@pytest.mark.contract
def test_main_exits_nonzero_on_download_failure(monkeypatch, tmp_path):
    """Aiuti: se un file non si scarica, main() esce 1."""

    def boom(url, tmp_dir, chunk_size=50000):
        raise RuntimeError("simulated HTTP 500")

    monkeypatch.setattr(full_batch, "process_url", boom)
    monkeypatch.setattr(
        sys, "argv",
        ["full_batch.py", "--from", "2026", "--to", "2026", "-o", str(tmp_path)],
    )
    with pytest.raises(SystemExit) as exc:
        full_batch.main()
    assert exc.value.code == 1


@pytest.mark.contract
def test_run_misure_exits_nonzero_on_download_failure(monkeypatch, tmp_path):
    """Misure: se un file non si scarica, _run_misure() esce 1."""

    def boom(url):
        raise RuntimeError("simulated HTTP 500")

    monkeypatch.setattr(full_batch, "process_misura_url", boom)
    monkeypatch.setattr(
        sys, "argv",
        ["full_batch.py", "--misure", "-o", str(tmp_path)],
    )
    with pytest.raises(SystemExit) as exc:
        full_batch.main()
    assert exc.value.code == 1
