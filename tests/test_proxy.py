"""Proxy ``BLOCKED_SOURCE_PROXY``: le richieste passano dal proxy se configurato.

Alcune fonti bloccano gli IP dei runner GitHub con un connect timeout (non 403):
quando la variabile è impostata, ``full_batch`` deve instradare lì le richieste.
"""

from __future__ import annotations

import importlib.util
import sys
import urllib.request
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
PROXY = "http://proxy.test:8888"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


full_batch = _load_module("rna_full_batch_proxy", "full_batch.py")


def _proxy_map(opener) -> dict:
    for h in opener.handlers:
        if isinstance(h, urllib.request.ProxyHandler):
            return h.proxies
    return {}


@pytest.mark.contract
def test_opener_uses_blocked_source_proxy(monkeypatch):
    monkeypatch.setenv("BLOCKED_SOURCE_PROXY", PROXY)
    proxies = _proxy_map(full_batch._opener())
    assert proxies.get("http") == PROXY
    assert proxies.get("https") == PROXY


@pytest.mark.contract
def test_opener_without_proxy(monkeypatch):
    monkeypatch.delenv("BLOCKED_SOURCE_PROXY", raising=False)
    assert PROXY not in _proxy_map(full_batch._opener()).values()
