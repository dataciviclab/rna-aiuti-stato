"""Download RNA via ZIP: derivazione URL, stream del membro, fallback XML.

Lo ZIP è ~30x più piccolo dell'XML, è servito dove l'XML risponde 500, e il
CRC-32 rileva i troncamenti che ``recover=True`` maschererebbe.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import zipfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

XML_URL = "https://www.incentivitalia.gov.it/open-data/aiuti/OpenData_Aiuti_2017_01.xml"
ZIP_URL = "https://www.incentivitalia.gov.it/open-data/aiuti/OpenData_Aiuti_2017_01.zip"
XML_BODY = (
    b'<?xml version="1.0"?>'
    b'<LISTA_AIUTI xmlns="http://www.rna.it/RNA_aiuto/schema"/>'
)


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


full_batch = _load_module("rna_full_batch_zip", "full_batch.py")


def _make_zip(content: bytes = XML_BODY, name: str = "OpenData_Aiuti_2017_01.xml") -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, content)
    return bio.getvalue()


# ---------------------------------------------------------------------------
# Derivazione URL e stream del membro
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_zip_url_derivation():
    assert full_batch._zip_url(XML_URL) == ZIP_URL


@pytest.mark.contract
def test_zip_url_rejects_non_xml():
    with pytest.raises(ValueError):
        full_batch._zip_url("https://example.org/file.csv")


@pytest.mark.contract
def test_zip_member_stream_reads_xml():
    stream = full_batch._ZipMemberStream(_make_zip())
    assert stream.read() == XML_BODY


@pytest.mark.contract
def test_zip_member_stream_rejects_zip_without_xml():
    with pytest.raises(zipfile.BadZipFile):
        full_batch._ZipMemberStream(_make_zip(content=b"x", name="readme.txt"))


# ---------------------------------------------------------------------------
# _download_with_retry: ZIP-first + fallback
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_download_prefers_zip(monkeypatch):
    monkeypatch.setattr(full_batch, "_with_retry", lambda url, fetch: _make_zip())
    stream = full_batch._download_with_retry(XML_URL)
    assert stream.read() == XML_BODY


@pytest.mark.contract
def test_download_404_is_month_not_published(monkeypatch):
    def fake_retry(url, fetch):
        raise full_batch.MonthNotPublished(url)

    monkeypatch.setattr(full_batch, "_with_retry", fake_retry)
    with pytest.raises(full_batch.MonthNotPublished):
        full_batch._download_with_retry(XML_URL)


@pytest.mark.contract
def test_download_falls_back_when_zip_unavailable(monkeypatch):
    sentinel = object()

    def fake_retry(url, fetch):
        raise RuntimeError("HTTP 500")

    monkeypatch.setattr(full_batch, "_with_retry", fake_retry)
    monkeypatch.setattr(full_batch, "_open_xml", lambda url: sentinel)
    assert full_batch._download_with_retry(XML_URL) is sentinel


@pytest.mark.contract
def test_download_falls_back_when_zip_corrupt(monkeypatch):
    sentinel = object()

    def fake_retry(url, fetch):
        return b"non e' uno zip"

    monkeypatch.setattr(full_batch, "_with_retry", fake_retry)
    monkeypatch.setattr(full_batch, "_open_xml", lambda url: sentinel)
    assert full_batch._download_with_retry(XML_URL) is sentinel
