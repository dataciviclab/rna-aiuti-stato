"""Parser RNA — estrazione XML + schema + I/O parquet.

Modulo centrale del pacchetto ``rna_aiuti``. Contiene:
- Funzioni pure di parsing XML (``flatten_aiuto``, ``extract_aiuto_base``, …)
- Schema dati (``SCHEMA``, ``FIELD_NAMES``) — *single source of truth*
- Filtri stream per pre-processing XML corrotto (``XMLCharFilter``, ``XMLTagFixer``)
- I/O Parquet (``write_partition``)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger("rna_aiuti")

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


# ---------------------------------------------------------------------------
# Misure RNA (OpenData_Misura_*.xml)
# ---------------------------------------------------------------------------

MISURA_NS = "{http://www.rna.it/RNA_misura/schema}"


def _misura_text(elem, tag: str) -> str:
    """Testo di un figlio diretto di una Misura (namespace RNA misura)."""
    child = elem.find(f"{MISURA_NS}{tag}")
    if child is None or child.text is None:
        return ""
    return " ".join(child.text.split())


def _misura_float(elem, tag: str) -> float | None:
    raw = _misura_text(elem, tag)
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except (ValueError, TypeError):
        return None


def extract_misura(misura_elem) -> dict:
    """Campi da un <MISURA>. Una misura = una riga."""
    anno, mese = 0, 0
    data_inizio = _misura_text(misura_elem, "DATA_INIZIO_MISURA")
    if data_inizio:
        anno, mese = parse_year_month(data_inizio[:10])

    return {
        "car": _misura_text(misura_elem, "CAR"),
        "car_padre": _misura_text(misura_elem, "CAR_PADRE"),
        "car_attivo": _misura_text(misura_elem, "CAR_ATTIVO"),
        "titolo_misura": _misura_text(misura_elem, "TITOLO_MISURA"),
        "des_tipo_misura": _misura_text(misura_elem, "DES_TIPO_MISURA"),
        "cod_tipo_misura": _misura_text(misura_elem, "COD_TIPO_MISURA"),
        "data_inizio_misura": data_inizio,
        "data_fine_misura": _misura_text(misura_elem, "DATA_FINE_MISURA"),
        "base_giuridica_nazionale": _misura_text(misura_elem, "BASE_GIURIDICA_NAZIONALE"),
        "stato_membro": _misura_text(misura_elem, "STATO_MEMBRO"),
        "cod_amm": _misura_text(misura_elem, "COD_AMM"),
        "des_autorita": _misura_text(misura_elem, "DES_AUTORITA"),
        "autorita_concedente": _misura_text(misura_elem, "AUTORITA_CONCEDENTE_TRASP_CE"),
        "importo_prestiti_garantiti": _misura_float(misura_elem, "IMPORTO_PRESTITI_GARANTITI"),
        "importo_aiuto_ad_hoc": _misura_float(misura_elem, "IMPORTO_AIUTO_AD_HOC"),
        "link_aiuto": _misura_text(misura_elem, "LINK_AIUTO"),
        "flag_quadro": _misura_text(misura_elem, "FLAG_QUADRO"),
        "flag_modifica_regime": _misura_text(misura_elem, "FLAG_MODIFICA_REGIME_O_ESISTENTE"),
        "anno": anno,
        "mese": mese,
    }


# ---------------------------------------------------------------------------
# Schema dati — single source of truth per colonne e tipi
# ---------------------------------------------------------------------------
# Allineato con dataset.yml. Se aggiungi/cambi un campo, aggiorna QUI
# e in dataset.yml; extract.py e full_batch.py lo importano da qui.

SCHEMA = pa.schema([
    # AIUTO (17 campi)
    pa.field("data_concessione", pa.string()),
    pa.field("car", pa.string()),
    pa.field("cor", pa.string()),
    pa.field("denominazione_beneficiario", pa.string()),
    pa.field("codice_fiscale_beneficiario", pa.string()),
    pa.field("tipo_beneficiario", pa.string()),
    pa.field("regione_beneficiario", pa.string()),
    pa.field("soggetto_concedente", pa.string()),
    pa.field("titolo_misura", pa.string()),
    pa.field("des_tipo_misura", pa.string()),
    pa.field("titolo_progetto", pa.string()),
    pa.field("descrizione_progetto", pa.string()),
    pa.field("cup", pa.string()),
    pa.field("atto_concessione", pa.string()),
    pa.field("base_giuridica_nazionale", pa.string()),
    pa.field("identificativo_ufficio", pa.string()),
    pa.field("link_trasparenza_nazionale", pa.string()),
    # COMPONENTE (8 campi)
    pa.field("id_componente", pa.string()),
    pa.field("procedimento", pa.string()),
    pa.field("cod_procedimento", pa.string()),
    pa.field("regolamento_ue", pa.string()),
    pa.field("cod_regolamento", pa.string()),
    pa.field("obiettivo", pa.string()),
    pa.field("cod_obiettivo", pa.string()),
    pa.field("settore_attivita", pa.string()),
    # STRUMENTO (4 campi)
    pa.field("cod_strumento", pa.string()),
    pa.field("strumento", pa.string()),
    pa.field("elemento_aiuto", pa.float64()),
    pa.field("importo_nominale", pa.float64()),
    # Partizione (2 campi)
    pa.field("anno", pa.int32()),
    pa.field("mese", pa.int32()),
])

FIELD_NAMES: list[str] = [f.name for f in SCHEMA]

DEDUP_KEY = ("cor", "id_componente", "cod_strumento")

# Schema Misure RNA
MISURA_SCHEMA = pa.schema([
    pa.field("car", pa.string()),
    pa.field("car_padre", pa.string()),
    pa.field("car_attivo", pa.string()),
    pa.field("titolo_misura", pa.string()),
    pa.field("des_tipo_misura", pa.string()),
    pa.field("cod_tipo_misura", pa.string()),
    pa.field("data_inizio_misura", pa.string()),
    pa.field("data_fine_misura", pa.string()),
    pa.field("base_giuridica_nazionale", pa.string()),
    pa.field("stato_membro", pa.string()),
    pa.field("cod_amm", pa.string()),
    pa.field("des_autorita", pa.string()),
    pa.field("autorita_concedente", pa.string()),
    pa.field("importo_prestiti_garantiti", pa.float64()),
    pa.field("importo_aiuto_ad_hoc", pa.float64()),
    pa.field("link_aiuto", pa.string()),
    pa.field("flag_quadro", pa.string()),
    pa.field("flag_modifica_regime", pa.string()),
    pa.field("anno", pa.int32()),
    pa.field("mese", pa.int32()),
])
MISURA_FIELD_NAMES: list[str] = [f.name for f in MISURA_SCHEMA]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def parse_year_month(data_concessione: str) -> tuple[int, int]:
    """Estrae anno e mese da una data concessione ISO (YYYY-MM-DD).

    Se manca il mese (es. solo ``"2023"``), restituisce ``(anno, 0)``.
    Se la stringa è vuota o non parsabile, restituisce ``(0, 0)``.
    """
    if not data_concessione:
        return 0, 0
    parts = data_concessione.split("-")
    try:
        anno = int(parts[0])
        mese = int(parts[1]) if len(parts) >= 2 else 0
        return anno, mese
    except (ValueError, IndexError):
        return 0, 0


def _to_table(rows: list[dict], schema: pa.Schema | None = None) -> pa.Table:
    """Converte una lista di dict in tabella PyArrow.

    Args:
        rows: Lista di dict con campi allineati allo schema.
        schema: Schema PyArrow da usare. Default SCHEMA (Aiuti).
    """
    if schema is None:
        schema = SCHEMA
    field_names = [f.name for f in schema]
    batch: dict[str, list] = {f: [] for f in field_names}
    for row in rows:
        for field in field_names:
            batch[field].append(row.get(field))
    return pa.Table.from_pydict(batch, schema=schema)


# ---------------------------------------------------------------------------
# Filtri stream per pre-processing XML
# ---------------------------------------------------------------------------


class XMLCharFilter:
    """Wrapper file-like che filtra caratteri XML non validi dallo stream.

    I file XML di RNA.gov.it possono contenere byte non validi per XML
    (es. caratteri di controllo < 0x20). Questo filtro li rimuove
    al volo durante lo streaming.
    """

    _ALLOWED = frozenset({0x09, 0x0A, 0x0D})

    def __init__(self, stream):
        self.stream = stream
        self._buf = b""

    def read(self, n: int = -1) -> bytes:
        if n == -1:
            data = self.stream.read()
        else:
            if len(self._buf) >= n:
                data = self._buf[:n]
                self._buf = self._buf[n:]
                return data
            data = self._buf + self.stream.read(n - len(self._buf))
            self._buf = b""
        if isinstance(data, bytes):
            return bytes(b for b in data if b >= 0x20 or b in self._ALLOWED)
        return data

    def readinto(self, b: bytearray) -> int:
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n

    def close(self):
        self.stream.close()


class XMLTagFixer:
    """Filtro stream che corregge tag RNA troncati nei file XML della fonte.

    Alcuni file XML di RNA.gov.it hanno tag troncati (es. ``BASE_GIURIDICA_NAZ``
    invece di ``BASE_GIURIDICA_NAZIONALE``). Il filtro bufferizza fino al
    prossimo ``>`` (fine tag XML) per non tagliare mai a metà un nome di tag,
    poi applica le correzioni con regex a contesto (negative lookahead):
    un nome troncato matcha solo se non è parte di un nome più lungo.

    Esempio: ``BASE_GIURIDICA_NAZ`` matcha (seguito da ``>``, spazio o ``/``),
    ma ``BASE_GIURIDICA_NAZIONALE`` NON matcha (seguito da ``IO...``).
    """

    # Pattern regex con negative lookahead: matcha solo se il nome troncato
    # NON è seguito da caratteri validi in un nome di tag ([A-Z_]).
    # Esempio:
    #   "<BASE_GIURIDICA_NAZ>"  → corretto  (seguito da >)
    #   "<IMPORTO_NOMINALE>"    → NON matcha (seguito da ALE)
    _PATTERNS = (
        (re.compile(rb"BASE_GIURIDICA_NAZ(?![A-Z_])"), b"BASE_GIURIDICA_NAZIONALE"),
        (re.compile(rb"IMPORTO_NOMIN(?![A-Z_])"), b"IMPORTO_NOMINALE"),
    )
    _MAX_FIX = max(len(p.pattern) for p, _ in _PATTERNS)

    def __init__(self, stream):
        self._stream = stream
        self._buf = b""

    def read(self, n: int = -1) -> bytes:
        if n == -1:
            data = self._buf + self._stream.read()
            self._buf = b""
        else:
            # Bufferizza almeno n + MAX_FIX byte (per safe crossing)
            while len(self._buf) < n + self._MAX_FIX:
                chunk = self._stream.read(4096)
                if not chunk:
                    break
                self._buf += chunk

            if not self._buf:
                return b""

            if len(self._buf) > n:
                # Taglia dopo l'ultimo '>' per non spezzare nomi di tag
                cut = self._buf.rfind(b">", 0, n + self._MAX_FIX)
                if cut >= 0:
                    data = self._buf[: cut + 1]
                    self._buf = self._buf[cut + 1 :]
                else:
                    data = self._buf[:n]
                    self._buf = self._buf[n:]
            else:
                data = self._buf
                self._buf = b""

        for pattern, replacement in self._PATTERNS:
            data = pattern.sub(replacement, data)
        return data

    def readinto(self, b: bytearray) -> int:
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n

    def close(self):
        self._stream.close()


# ---------------------------------------------------------------------------
# I/O Parquet
# ---------------------------------------------------------------------------


def write_partition(
    rows: list[dict],
    base_dir: str | Path,
    year: int,
    mode: str = "overwrite",
    dedup: bool = True,
    prefix: str = "rna",
    schema: pa.Schema | None = None,
) -> Path:
    """Scrive righe in un parquet annuale.

    Args:
        rows: Lista di dict con i campi allineati a SCHEMA.
        base_dir: Directory dei parquet annuali.
        year: Anno (2000-2099).
        mode: ``"overwrite"`` (default) sostituisce il file se esiste;
              ``"append"`` concatena al file esistente.
        dedup: Se True (default) e mode='overwrite', scarta righe con
               ``(cor, id_componente, cod_strumento)`` duplicate (tiene
               l'ultima occorrenza).

    Returns:
        Path del parquet scritto.
    """
    if schema is None:
        schema = SCHEMA
    if dedup and DEDUP_KEY and not all(k in [f.name for f in schema] for k in DEDUP_KEY):
        logger.warning("  dedup disabilitato: schema non ha i campi %s", DEDUP_KEY)
        dedup = False

    base_dir = Path(base_dir)
    out_path = base_dir / f"{prefix}_{year}.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    new_table = _to_table(rows, schema=schema)
    n_new = new_table.num_rows

    if mode == "overwrite":
        if dedup:
            new_table = _dedup_table(new_table)
        pq.write_table(new_table, str(out_path), compression="zstd")
        logger.info("  → %s: %d righe (scritto)", out_path.name, new_table.num_rows)
    elif mode == "append":
        if out_path.exists():
            old_table = pq.read_table(str(out_path))
            n_old = old_table.num_rows
            combined = pa.concat_tables([old_table, new_table])
            if dedup:
                combined = _dedup_table(combined)
            pq.write_table(combined, str(out_path), compression="zstd")
            logger.info("  → %s: %d righe (old %d + new %d → %d)",
                        out_path.name, combined.num_rows, n_old, n_new, combined.num_rows)
        else:
            if dedup:
                new_table = _dedup_table(new_table)
            pq.write_table(new_table, str(out_path), compression="zstd")
            logger.info("  → %s: %d righe (nuovo)", out_path.name, new_table.num_rows)
    else:
        raise ValueError(f"mode deve essere 'overwrite' o 'append', non {mode!r}")

    return out_path


def _dedup_table(table: pa.Table) -> pa.Table:
    """Dedup per chiave (cor, id_componente, cod_strumento): tiene l'ultima riga.

    Usa DuckDB se disponibile (molto più veloce su tabelle grandi),
    altrimenti pandas.
    """
    n_before = table.num_rows
    if n_before < 2:
        return table

    import pandas as pd

    df = table.to_pandas()
    n_before = len(df)
    df = df.drop_duplicates(
        subset=["cor", "id_componente", "cod_strumento"],
        keep="last",
    )
    n_after = len(df)
    if n_after < n_before:
        logger.info("    dedup: %d → %d righe", n_before, n_after)
    return pa.Table.from_pandas(df, schema=SCHEMA)


def extract_streaming(
    source: str | Path | Any,
    page_size: int = 5000,
) -> dict[int, list[dict]]:
    """Processa RNA XML in streaming, da file o da file-like object (HTTP).

    Args:
        source: Path del file XML **oppure** file-like object binario.
        page_size: Righe intermedie per log.

    Returns:
        Dict {anno: [righe]}.
    """
    import lxml.etree as ET

    t0 = __import__("time").time()
    total_aiuti = 0
    rows_by_year: dict[int, list[dict]] = {}

    TAG_AIUTO = _tag("AIUTO")

    if isinstance(source, (str, Path)):
        context = ET.iterparse(str(source), events=("end",), tag=TAG_AIUTO)
    else:
        context = ET.iterparse(source, events=("end",), tag=TAG_AIUTO)

    for _event, elem in context:
        total_aiuti += 1
        flat_rows = flatten_aiuto(elem)

        for row in flat_rows:
            anno, mese = parse_year_month(row.get("data_concessione", ""))
            row["anno"] = anno
            row["mese"] = mese
            rows_by_year.setdefault(anno, []).append(row)

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

        if total_aiuti % page_size == 0:
            logger.info("  %d aiuti processati ...", total_aiuti)

    elapsed = __import__("time").time() - t0
    total_rows = sum(len(v) for v in rows_by_year.values())
    logger.info("  %d aiuti → %d righe in %.1f sec (%.0f aiuti/sec)",
                total_aiuti, total_rows, elapsed, total_aiuti / elapsed if elapsed else 0)

    return rows_by_year


def summary(parquet_dir: str | Path):
    """Mostra riepilogo di tutti i parquet annuali."""
    parquet_dir = Path(parquet_dir)
    parquet_files = sorted(parquet_dir.glob("rna_*.parquet"))

    if not parquet_files:
        logger.info("Nessun parquet trovato in %s", parquet_dir)
        return

    logger.info("")
    logger.info("=== CATALOGO RNA PARQUET ===")
    logger.info("%-15s %10s %12s", "File", "Righe", "Dimensione")
    logger.info("-" * 40)

    total_rows = 0
    total_size = 0
    for pf in parquet_files:
        meta = pq.read_metadata(str(pf))
        n_rows = meta.num_rows
        size_mb = pf.stat().st_size / 1_000_000
        total_rows += n_rows
        total_size += size_mb
        logger.info("%-15s %10d %10.1f MB", pf.stem, n_rows, size_mb)

    logger.info("-" * 40)
    logger.info("%-15s %10d %10.1f MB", "TOTALE", total_rows, total_size)
