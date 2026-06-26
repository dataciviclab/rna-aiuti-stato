"""Test del parser RNA — su XML campione."""

from __future__ import annotations

from pathlib import Path

import lxml.etree as ET

from rna_aiuti.parser import flatten_aiuto, extract_aiuto_base, extract_componente, extract_strumento

NS = "{http://www.rna.it/RNA_aiuto/schema}"
HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "samples"


def _first_aiuto(xml_bytes: bytes):
    """Estrae il primo <AIUTO> da XML."""
    import io
    context = ET.iterparse(io.BytesIO(xml_bytes), events=("end",), tag=f"{NS}AIUTO")
    for _event, elem in context:
        return elem
    return None


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


def test_parse_aiuto_base():
    """Verifica estrazione campi AIUTO."""
    aiuto = _first_aiuto(SAMPLE_XML)
    assert aiuto is not None, "Nessun AIUTO trovato nel campione"
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

    # Prima riga: Sovvenzione
    assert rows[0]["strumento"] == "Sovvenzione"
    assert rows[0]["elemento_aiuto"] == 10000.0
    assert rows[0]["importo_nominale"] == 10000.0
    assert rows[0]["procedimento"] == "De Minimis"
    assert rows[0]["settore_attivita"] == "(NACE 2) J.62.0"
    assert rows[0]["codice_fiscale_beneficiario"] == "01234567890"

    # Seconda riga: Prestito
    assert rows[1]["strumento"] == "Prestito"
    assert rows[1]["elemento_aiuto"] == 5000.0
    assert rows[1]["importo_nominale"] == 50000.0


def test_parse_no_componenti():
    """Verifica AIUTO senza COMPONENTI produce 1 riga con campi vuoti."""
    xml = SAMPLE_XML.replace(b"<COMPONENTI_AIUTO>", b"<!-- NO -->").replace(
        b"<COMPONENTE_AIUTO>", b"<!-- NO -->"
    ).replace(b"</COMPONENTI_AIUTO>", b"<!-- NO -->").replace(
        b"</COMPONENTE_AIUTO>", b"<!-- NO -->"
    )
    # Fix: remove the nested content entirely
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


def test_all_29_fields_present():
    """Verifica che una riga flatten contenga tutti i 29 campi dello schema."""
    aiuto = _first_aiuto(SAMPLE_XML)
    rows = flatten_aiuto(aiuto)
    expected_fields = {
        "data_concessione", "car", "cor",
        "denominazione_beneficiario", "codice_fiscale_beneficiario",
        "tipo_beneficiario", "regione_beneficiario", "soggetto_concedente",
        "titolo_misura", "des_tipo_misura", "titolo_progetto",
        "descrizione_progetto", "cup", "atto_concessione",
        "base_giuridica_nazionale", "identificativo_ufficio",
        "link_trasparenza_nazionale",
        "id_componente", "procedimento", "cod_procedimento",
        "regolamento_ue", "cod_regolamento", "obiettivo", "cod_obiettivo",
        "settore_attivita",
        "cod_strumento", "strumento", "elemento_aiuto", "importo_nominale",
    }
    assert set(rows[0].keys()) == expected_fields, (
        f"Field mismatch. Extra: {set(rows[0].keys()) - expected_fields}. "
        f"Missing: {expected_fields - set(rows[0].keys())}"
    )
