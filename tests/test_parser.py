"""Test del parser RNA — parsing XML, schema, filtri stream, I/O parquet."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import lxml.etree as ET
import pyarrow as pa
import pyarrow.parquet as pq

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
    _to_table,
    parse_year_month,
    # Stream filter
    XMLCharFilter,
    XMLTagFixer,
)

NS = "{http://www.rna.it/RNA_aiuto/schema}"

SAMPLE_XML = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<LISTA_AIUTI xmlns="http://www.rna.it/RNA_aiuto/schema">
    <AIUTO>
        <CAR>999</CAR>
        <TITOLO_MISURA>Test misura</TITOLO_MISURA>
        <DES_TIPO_MISURA>Regime di aiuti</DES_TIPO_MISURA>
        <BASE_GIURIDICA_NAZIONALE>Legge test</BASE_GIURIDICA_NAZIONALE>
        <IDENTIFICATIVO_UFFICIO>12345</IDENTIFICATIVO_UFFICIO>
        <SOGGETTO_CONCEDENTE>Test concedente</SOGGETTO_CONCEDENTE>
        <COR>777</COR>
        <TITOLO_PROGETTO>Test progetto</TITOLO_PROGETTO>
        <DESCRIZIONE_PROGETTO>Descrizione test</DESCRIZIONE_PROGETTO>
        <LINK_TRASPARENZA_NAZIONALE>https://test.it</LINK_TRASPARENZA_NAZIONALE>
        <DATA_CONCESSIONE>2023-06-15</DATA_CONCESSIONE>
        <CUP>TESTCUP123</CUP>
        <ATTO_CONCESSIONE>det. n. 1</ATTO_CONCESSIONE>
        <DENOMINAZIONE_BENEFICIARIO>AZIENDA TEST SRL</DENOMINAZIONE_BENEFICIARIO>
        <CODICE_FISCALE_BENEFICIARIO>01234567890</CODICE_FISCALE_BENEFICIARIO>
        <DES_TIPO_BENEFICIARIO>PMI</DES_TIPO_BENEFICIARIO>
        <REGIONE_BENEFICIARIO>Lazio</REGIONE_BENEFICIARIO>
        <COMPONENTI_AIUTO>
            <COMPONENTE_AIUTO>
                <ID_COMPONENTE_AIUTO>555</ID_COMPONENTE_AIUTO>
                <COD_PROCEDIMENTO>1</COD_PROCEDIMENTO>
                <DES_PROCEDIMENTO>De Minimis</DES_PROCEDIMENTO>
                <COD_REGOLAMENTO>CE1407/13</COD_REGOLAMENTO>
                <DES_REGOLAMENTO>Reg. UE 1407/2013 de minimis</DES_REGOLAMENTO>
                <COD_OBIETTIVO>100200</COD_OBIETTIVO>
                <DES_OBIETTIVO>Sviluppo regionale</DES_OBIETTIVO>
                <SETTORE_ATTIVITA>(NACE 2) J.62.0</SETTORE_ATTIVITA>
                <STRUMENTI_AIUTO>
                    <STRUMENTO_AIUTO>
                        <COD_STRUMENTO>2</COD_STRUMENTO>
                        <DES_STRUMENTO>Sovvenzione</DES_STRUMENTO>
                        <ELEMENTO_DI_AIUTO>10000.00</ELEMENTO_DI_AIUTO>
                        <IMPORTO_NOMINALE>10000.00</IMPORTO_NOMINALE>
                    </STRUMENTO_AIUTO>
                    <STRUMENTO_AIUTO>
                        <COD_STRUMENTO>7</COD_STRUMENTO>
                        <DES_STRUMENTO>Prestito</DES_STRUMENTO>
                        <ELEMENTO_DI_AIUTO>5000.00</ELEMENTO_DI_AIUTO>
                        <IMPORTO_NOMINALE>50000.00</IMPORTO_NOMINALE>
                    </STRUMENTO_AIUTO>
                </STRUMENTI_AIUTO>
            </COMPONENTE_AIUTO>
        </COMPONENTI_AIUTO>
    </AIUTO>
</LISTA_AIUTI>
"""


def _first_aiuto(xml_bytes: bytes):
    """Estrae il primo <AIUTO> da XML."""
    context = ET.iterparse(io.BytesIO(xml_bytes), events=("end",), tag=f"{NS}AIUTO")
    for _event, elem in context:
        return elem
    return None


# ---------------------------------------------------------------------------
# Parsing XML
# ---------------------------------------------------------------------------


def test_parse_aiuto_base():
    """Verifica estrazione campi AIUTO."""
    aiuto = _first_aiuto(SAMPLE_XML)
    assert aiuto is not None
    base = extract_aiuto_base(aiuto)
    assert base["car"] == "999"
    assert base["cor"] == "777"
    assert base["denominazione_beneficiario"] == "AZIENDA TEST SRL"
    assert base["codice_fiscale_beneficiario"] == "01234567890"
    assert base["tipo_beneficiario"] == "PMI"
    assert base["regione_beneficiario"] == "Lazio"
    assert base["soggetto_concedente"] == "Test concedente"
    assert base["data_concessione"] == "2023-06-15"
    assert base["cup"] == "TESTCUP123"
    assert base["identificativo_ufficio"] == "12345"
    assert base["link_trasparenza_nazionale"] == "https://test.it"
    assert base["titolo_misura"] == "Test misura"
    assert base["des_tipo_misura"] == "Regime di aiuti"
    assert base["base_giuridica_nazionale"] == "Legge test"
    assert base["titolo_progetto"] == "Test progetto"
    assert base["descrizione_progetto"] == "Descrizione test"
    assert base["atto_concessione"] == "det. n. 1"


def test_parse_flatten():
    """Verifica flatten: 1 AIUTO × 1 COMPONENTE × 2 STRUMENTI = 2 righe."""
    aiuto = _first_aiuto(SAMPLE_XML)
    rows = flatten_aiuto(aiuto)
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
    assert rows[0]["strumento"] == "Sovvenzione"
    assert rows[0]["elemento_aiuto"] == 10000.0
    assert rows[0]["importo_nominale"] == 10000.0
    assert rows[0]["procedimento"] == "De Minimis"
    assert rows[0]["settore_attivita"] == "(NACE 2) J.62.0"
    assert rows[1]["strumento"] == "Prestito"
    assert rows[1]["elemento_aiuto"] == 5000.0
    assert rows[1]["importo_nominale"] == 50000.0


def test_parse_no_componenti():
    """Verifica AIUTO senza COMPONENTI produce 1 riga con campi vuoti."""
    xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<LISTA_AIUTI xmlns="http://www.rna.it/RNA_aiuto/schema">
    <AIUTO>
        <CAR>1</CAR>
        <TITOLO_MISURA>Test</TITOLO_MISURA>
        <DES_TIPO_MISURA>Regime</DES_TIPO_MISURA>
        <DENOMINAZIONE_BENEFICIARIO>AZIENDA TEST</DENOMINAZIONE_BENEFICIARIO>
        <CODICE_FISCALE_BENEFICIARIO>01234567890</CODICE_FISCALE_BENEFICIARIO>
        <REGIONE_BENEFICIARIO>Lazio</REGIONE_BENEFICIARIO>
        <SOGGETTO_CONCEDENTE>Test</SOGGETTO_CONCEDENTE>
        <DATA_CONCESSIONE>2023-06-15</DATA_CONCESSIONE>
    </AIUTO>
</LISTA_AIUTI>
"""
    aiuto = _first_aiuto(xml)
    rows = flatten_aiuto(aiuto)
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
    assert rows[0]["denominazione_beneficiario"] == "AZIENDA TEST"
    assert rows[0]["elemento_aiuto"] is None
    assert rows[0]["strumento"] == ""


def test_all_fields_present():
    """Verifica che una riga flatten contenga tutti i campi dello schema."""
    aiuto = _first_aiuto(SAMPLE_XML)
    rows = flatten_aiuto(aiuto)
    expected_fields = set(FIELD_NAMES) - {"anno", "mese"}
    assert set(rows[0].keys()) == expected_fields, (
        f"Extra: {set(rows[0].keys()) - expected_fields}. "
        f"Missing: {expected_fields - set(rows[0].keys())}"
    )


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_schema_has_31_fields():
    """Lo schema ha 31 campi: 17 AIUTO + 8 COMPONENTE + 4 STRUMENTO + 2 partizione."""
    assert len(SCHEMA) == 31, f"Expected 31 fields, got {len(SCHEMA)}"
    assert FIELD_NAMES == [f.name for f in SCHEMA]


def test_schema_matches_dataset_yml():
    """Verifica che i campi critici dello schema siano allineati con DEDUP_KEY."""
    for key_field in DEDUP_KEY:
        assert key_field in FIELD_NAMES, f"{key_field} mancante da FIELD_NAMES"


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def test_parse_year_month():
    assert parse_year_month("2023-06-15") == (2023, 6)
    assert parse_year_month("") == (0, 0)
    assert parse_year_month("2023") == (2023, 0)
    assert parse_year_month("invalid") == (0, 0)


# ---------------------------------------------------------------------------
# Filtri stream
# ---------------------------------------------------------------------------


def test_xml_char_filter_removes_bad_chars():
    """XMLCharFilter rimuove byte di controllo < 0x20 (tranne TAB, LF, CR)."""
    raw = b"<root>\x00\x01\x02</root>"
    f = XMLCharFilter(io.BytesIO(raw))
    assert f.read() == b"<root></root>", f"Got {f.read()!r}"


def test_xml_char_filter_keeps_allowed():
    """TAB, LF, CR vengono tenuti."""
    raw = b"<root>\x09\x0A\x0D</root>"
    f = XMLCharFilter(io.BytesIO(raw))
    assert f.read() == raw


def test_tag_fixer_fixes_base_giuridica_naz():
    """XMLTagFixer corregge BASE_GIURIDICA_NAZ → BASE_GIURIDICA_NAZIONALE."""
    xml = b"<AIUTO><BASE_GIURIDICA_NAZ>test</BASE_GIURIDICA_NAZ></AIUTO>"
    f = XMLTagFixer(io.BytesIO(xml))
    result = f.read()
    assert b"BASE_GIURIDICA_NAZIONALE" in result


def test_tag_fixer_fixes_importo_nomin():
    """XMLTagFixer corregge IMPORTO_NOMIN → IMPORTO_NOMINALE."""
    xml = b"<AIUTO><IMPORTO_NOMIN>1000</IMPORTO_NOMIN></AIUTO>"
    f = XMLTagFixer(io.BytesIO(xml))
    result = f.read()
    assert b"IMPORTO_NOMINALE" in result


def test_tag_fixer_chunk_crossing():
    """Tag troncato a cavallo tra chunk viene corretto."""
    xml = b"<test><BASE_GIURIDICA_NAZ>val</BASE_GIURIDICA_NAZ></test>"
    f = XMLTagFixer(io.BytesIO(xml))
    r1 = f.read(10)
    r2 = f.read(50)
    combined = r1 + r2
    assert b"BASE_GIURIDICA_NAZIONALE" in combined


def test_tag_fixer_leaves_regular_tags():
    """Tag normali non vengono alterati."""
    xml = b"<AIUTO><CAR>123</CAR></AIUTO>"
    f = XMLTagFixer(io.BytesIO(xml))
    result = f.read()
    assert b"<CAR>" in result


def test_tag_fixer_integration_lxml():
    """XML corretto da TagFixer viene parsato correttamente da lxml."""
    xml = b"""<?xml version="1.0"?>
<LISTA_AIUTI xmlns="http://www.rna.it/RNA_aiuto/schema">
  <AIUTO>
    <CAR>1</CAR>
    <BASE_GIURIDICA_NAZ>Legge</BASE_GIURIDICA_NAZ>
    <IMPORTO_NOMIN>50000</IMPORTO_NOMIN>
  </AIUTO>
</LISTA_AIUTI>"""
    f = XMLTagFixer(XMLCharFilter(io.BytesIO(xml)))
    ctx = ET.iterparse(f, events=("end",), tag=f"{NS}AIUTO", recover=True)
    count = 0
    for _ev, el in ctx:
        count += 1
        bg = el.find(f"{NS}BASE_GIURIDICA_NAZIONALE")
        imp = el.find(f"{NS}IMPORTO_NOMINALE")
        assert bg is not None, "BASE_GIURIDICA_NAZIONALE non trovato dopo fix"
        assert imp is not None, "IMPORTO_NOMINALE non trovato dopo fix"
    assert count == 1


def test_xml_char_filter_and_tag_fixer_chain():
    """I due filtri in cascata funzionano."""
    raw = b"<root>\x00<BASE_GIURIDICA_NAZ>x</BASE_GIURIDICA_NAZ>\x01</root>"
    f = XMLTagFixer(XMLCharFilter(io.BytesIO(raw)))
    result = f.read()
    assert b"\x00" not in result
    assert b"\x01" not in result
    assert b"BASE_GIURIDICA_NAZIONALE" in result


# ---------------------------------------------------------------------------
# I/O Parquet
# ---------------------------------------------------------------------------


def test_to_table_roundtrip():
    """_to_table converte dict in tabella PyArrow."""
    rows = [
        {"data_concessione": "2023-06-15", "car": "1", "cor": "10",
         "denominazione_beneficiario": "A", "codice_fiscale_beneficiario": "CF1",
         "tipo_beneficiario": "PMI", "regione_beneficiario": "Lazio",
         "soggetto_concedente": "Test", "titolo_misura": "M1",
         "des_tipo_misura": "Regime", "titolo_progetto": "", "descrizione_progetto": "",
         "cup": "", "atto_concessione": "", "base_giuridica_nazionale": "",
         "identificativo_ufficio": "", "link_trasparenza_nazionale": "",
         "id_componente": "C1", "procedimento": "De Minimis",
         "cod_procedimento": "1", "regolamento_ue": "", "cod_regolamento": "",
         "obiettivo": "", "cod_obiettivo": "", "settore_attivita": "",
         "cod_strumento": "2", "strumento": "Sovvenzione",
         "elemento_aiuto": 10000.0, "importo_nominale": 10000.0,
         "anno": 2023, "mese": 6},
    ]
    table = _to_table(rows)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 1
    assert table.num_columns == 31


def test_write_partition_overwrite(tmp_path: Path):
    """write_partition con mode='overwrite' sostituisce il file."""
    rows = _make_sample_rows(2023, "CF1")
    p = write_partition(rows, tmp_path, 2023, mode="overwrite")
    assert p.exists()
    n1 = pq.read_metadata(str(p)).num_rows
    assert n1 == 1

    # Second write con CF diverso: sovrascrive
    rows2 = _make_sample_rows(2023, "CF2")
    write_partition(rows2, tmp_path, 2023, mode="overwrite")
    n2 = pq.read_metadata(str(p)).num_rows
    assert n2 == 1, f"Overwrite: expected 1 row, got {n2}"

    # Verifica che il contenuto sia quello del secondo write
    tbl = pq.read_table(str(p))
    cf = tbl.column("codice_fiscale_beneficiario").to_pylist()
    assert cf == ["CF2"], f"Overwrite: expected CF2, got {cf}"


def test_write_partition_append(tmp_path: Path):
    """write_partition con mode='append' concatena."""
    rows = _make_sample_rows(2023, "CF1")
    p = write_partition(rows, tmp_path, 2023, mode="append")
    n1 = pq.read_metadata(str(p)).num_rows

    # Seconda riga con DEDUP_KEY diversa (cor=20, id_componente=C2)
    rows2 = [dict(_make_sample_rows(2023, "CF2")[0], cor="20", id_componente="C2")]
    write_partition(rows2, tmp_path, 2023, mode="append")
    n2 = pq.read_metadata(str(p)).num_rows
    assert n2 == n1 + 1, f"Append fallito: {n1} → {n2}"


def test_write_partition_dedup(tmp_path: Path):
    """Dedup rimuove righe con stessa (cor, id_componente, cod_strumento)."""
    rows = _make_sample_rows(2023, "CF1")  # cor=10, id_componente=C1, cod_strumento=2
    p = write_partition(rows, tmp_path, 2023, mode="overwrite", dedup=True)
    n1 = pq.read_metadata(str(p)).num_rows  # 1 riga

    # Seconda scrittura stessi dati (stessa chiave) → dedup le scarta
    write_partition(rows, tmp_path, 2023, mode="append", dedup=True)
    n2 = pq.read_metadata(str(p)).num_rows
    assert n2 == n1, f"Dedup fallito: {n1} → {n2}"  # deve restare 1


def test_dedup_key_fields_exist():
    """I campi della dedup key esistono nello schema."""
    for k in DEDUP_KEY:
        assert k in FIELD_NAMES, f"{k} non in FIELD_NAMES"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample_rows(year: int, cf: str) -> list[dict]:
    """Crea una riga di test valida per l'anno specificato."""
    return [{
        "data_concessione": f"{year}-06-15",
        "car": "1",
        "cor": "10",
        "denominazione_beneficiario": "Azienda",
        "codice_fiscale_beneficiario": cf,
        "tipo_beneficiario": "PMI",
        "regione_beneficiario": "Lazio",
        "soggetto_concedente": "Test",
        "titolo_misura": "M1",
        "des_tipo_misura": "Regime",
        "titolo_progetto": "",
        "descrizione_progetto": "",
        "cup": "",
        "atto_concessione": "",
        "base_giuridica_nazionale": "",
        "identificativo_ufficio": "",
        "link_trasparenza_nazionale": "",
        "id_componente": "C1",
        "procedimento": "De Minimis",
        "cod_procedimento": "1",
        "regolamento_ue": "",
        "cod_regolamento": "",
        "obiettivo": "",
        "cod_obiettivo": "",
        "settore_attivita": "",
        "cod_strumento": "2",
        "strumento": "Sovvenzione",
        "elemento_aiuto": 10000.0,
        "importo_nominale": 10000.0,
        "anno": year,
        "mese": 6,
    }]
