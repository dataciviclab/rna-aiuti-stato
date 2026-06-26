"""Parser RNA — funzioni pure di estrazione da XML.

Tutte le funzioni in questo modulo sono pure: non fanno I/O,
non dipendono da rete o filesystem. Prendono un elemento lxml
``<AIUTO>`` e restituiscono dati estratti.
"""

from __future__ import annotations

from typing import Any, Iterator

NS = "{http://www.rna.it/RNA_aiuto/schema}"


def _tag(name: str) -> str:
    """Qualifica un tag locale con il namespace RNA."""
    return f"{NS}{name}"


def _text(elem: Any, tag: str) -> str:
    """Testo di un figlio diretto, normalizzato."""
    child = elem.find(_tag(tag))
    if child is None or child.text is None:
        return ""
    return " ".join(child.text.split())


def _float_or_none(elem: Any, tag: str) -> float | None:
    """Valore numerico di un figlio, o None se assente/vuoto."""
    raw = _text(elem, tag)
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Estrazione campi AIUTO (livello 1)
# ---------------------------------------------------------------------------


def extract_aiuto_base(aiuto_elem: Any) -> dict[str, Any]:
    """Campi semplici 1:1 dall'elemento <AIUTO>."""
    return {
        "data_concessione": _text(aiuto_elem, "DATA_CONCESSIONE"),
        "car": _text(aiuto_elem, "CAR"),
        "cor": _text(aiuto_elem, "COR"),
        "denominazione_beneficiario": _text(aiuto_elem, "DENOMINAZIONE_BENEFICIARIO"),
        "codice_fiscale_beneficiario": _text(aiuto_elem, "CODICE_FISCALE_BENEFICIARIO"),
        "tipo_beneficiario": _text(aiuto_elem, "DES_TIPO_BENEFICIARIO"),
        "regione_beneficiario": _text(aiuto_elem, "REGIONE_BENEFICIARIO"),
        "soggetto_concedente": _text(aiuto_elem, "SOGGETTO_CONCEDENTE"),
        "titolo_misura": _text(aiuto_elem, "TITOLO_MISURA"),
        "des_tipo_misura": _text(aiuto_elem, "DES_TIPO_MISURA"),
        "titolo_progetto": _text(aiuto_elem, "TITOLO_PROGETTO"),
        "descrizione_progetto": _text(aiuto_elem, "DESCRIZIONE_PROGETTO"),
        "cup": _text(aiuto_elem, "CUP"),
        "atto_concessione": _text(aiuto_elem, "ATTO_CONCESSIONE"),
        "base_giuridica_nazionale": _text(aiuto_elem, "BASE_GIURIDICA_NAZIONALE"),
        "identificativo_ufficio": _text(aiuto_elem, "IDENTIFICATIVO_UFFICIO"),
        "link_trasparenza_nazionale": _text(aiuto_elem, "LINK_TRASPARENZA_NAZIONALE"),
    }


# ---------------------------------------------------------------------------
# Estrazione COMPONENTI_AIUTO (livello 2) e STRUMENTI_AIUTO (livello 3)
# ---------------------------------------------------------------------------


def extract_componente(comp_elem: Any) -> dict[str, Any]:
    """Campi da un <COMPONENTE_AIUTO>."""
    return {
        "id_componente": _text(comp_elem, "ID_COMPONENTE_AIUTO"),
        "procedimento": _text(comp_elem, "DES_PROCEDIMENTO"),
        "cod_procedimento": _text(comp_elem, "COD_PROCEDIMENTO"),
        "regolamento_ue": _text(comp_elem, "DES_REGOLAMENTO"),
        "cod_regolamento": _text(comp_elem, "COD_REGOLAMENTO"),
        "obiettivo": _text(comp_elem, "DES_OBIETTIVO"),
        "cod_obiettivo": _text(comp_elem, "COD_OBIETTIVO"),
        "settore_attivita": _text(comp_elem, "SETTORE_ATTIVITA"),
    }


def extract_strumento(stru_elem: Any) -> dict[str, Any]:
    """Campi da uno <STRUMENTO_AIUTO>."""
    return {
        "cod_strumento": _text(stru_elem, "COD_STRUMENTO"),
        "strumento": _text(stru_elem, "DES_STRUMENTO"),
        "elemento_aiuto": _float_or_none(stru_elem, "ELEMENTO_DI_AIUTO"),
        "importo_nominale": _float_or_none(stru_elem, "IMPORTO_NOMINALE"),
    }


# ---------------------------------------------------------------------------
# Flatten completo: un AIUTO → N righe (una per STRUMENTO)
# ---------------------------------------------------------------------------


def flatten_aiuto(aiuto_elem: Any) -> list[dict[str, Any]]:
    """Appiattisce un <AIUTO> in una lista di righe (una per STRUMENTO).

    Ogni riga contiene: campi AIUTO + campi COMPONENTE + campi STRUMENTO.
    Se un AIUTO non ha COMPONENTI o STRUMENTI, restituisce una riga
    con i soli campi AIUTO (i numerici saranno None).
    """
    base = extract_aiuto_base(aiuto_elem)
    rows: list[dict[str, Any]] = []

    comps = aiuto_elem.findall(_tag("COMPONENTI_AIUTO") + "/" + _tag("COMPONENTE_AIUTO"))

    # Default vuoti per tutti i campi non-AIUTO
    _empty_comp = {
        "id_componente": "",
        "procedimento": "",
        "cod_procedimento": "",
        "regolamento_ue": "",
        "cod_regolamento": "",
        "obiettivo": "",
        "cod_obiettivo": "",
        "settore_attivita": "",
    }
    _empty_stru = {
        "cod_strumento": "",
        "strumento": "",
        "elemento_aiuto": None,
        "importo_nominale": None,
    }

    if not comps:
        row = dict(base)
        row.update(_empty_comp)
        row.update(_empty_stru)
        rows.append(row)
        return rows

    for comp in comps:
        comp_data = extract_componente(comp)
        strums = comp.findall(_tag("STRUMENTI_AIUTO") + "/" + _tag("STRUMENTO_AIUTO"))

        if not strums:
            row = dict(base)
            row.update(comp_data)
            row.update(_empty_stru)
            rows.append(row)
            continue

        for stru in strums:
            row = dict(base)
            row.update(comp_data)
            row.update(extract_strumento(stru))
            rows.append(row)

    return rows
