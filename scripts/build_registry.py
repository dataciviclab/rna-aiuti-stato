"""Genera registry/registry.json (fusion ADR, toolkit v1.49.0).

Wrapper sottile sul builder condiviso ``toolkit.registry``: qui solo layout,
path contract e scrittura.

Layout rna-aiuti-stato:
- dataset.yml in ``datasets/*/`` (aiuti + misure);
- parquet e run records in ``out/data/`` (root dichiarato nei dataset.yml);
- raw dei dataset = parquet locali prodotti da full_batch.py (data/derived/);
- GCS: ``gs://dataciviclab-{clean,mart}/rna_aiuti_stato/{slug}/{year}/`` (layout year).

Usage:
    python scripts/build_registry.py            # dry-run (stampa riepilogo)
    python scripts/build_registry.py --write    # scrive in registry/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "registry"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--write",
        action="store_true",
        help="Scrive gli artifact in registry/ (default: dry-run)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Dir di output (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()

    try:
        from toolkit.registry import PathContract, RepoLayout
        from toolkit.registry.builders import build_registry
    except ImportError as exc:  # pragma: no cover
        print(
            f"ERRORE: toolkit.registry non disponibile ({exc}).\n"
            "Serve toolkit >= v1.48.1 (modulo registry su main).",
            file=sys.stderr,
        )
        return 1

    layout = RepoLayout(
        repo_root=ROOT,
        dataset_dirs=("datasets",),
        source_repo="dataciviclab/rna-aiuti-stato",
    )
    # prefix vuoto: i slug (rna_aiuti_stato, rna_misure) sono già a root del
    # bucket, coerenti con i path pubblicati da dataset-incubator:
    # gs://dataciviclab-{clean,mart}/<slug>/{year}/...
    contract = PathContract(clean_layout="year", mart_layout="year")

    existing = None
    existing_path = args.out / "registry.json"
    if existing_path.is_file():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(
                "WARN: registry.json esistente illeggibile — riparto da zero",
                file=sys.stderr,
            )

    result = build_registry(
        layout,
        path_contract=contract,
        existing_catalog={"datasets": existing.get("datasets", [])} if existing else None,
        existing_signals={"signals": existing.get("signals", [])} if existing else None,
    )

    # Errori già categorizzati dal builder: derive = warning (checkout
    # parziali), validation = bloccanti (artifact non conforme allo schema).
    all_warnings: list[str] = []
    all_real: list[str] = []
    for artifact, errors in result["errors"].items():
        all_warnings.extend(f"{artifact}: {e}" for e in errors["derive"])
        all_real.extend(f"{artifact}: {e}" for e in errors["validation"])

    for w in all_warnings:
        print(f"WARN: {w}", file=sys.stderr)

    if all_real:
        for e in all_real:
            print(f"ERROR: {e}", file=sys.stderr)
        print("Artifact NON scritti: errori di validazione.", file=sys.stderr)
        return 1

    registry = result["registry"]
    if not args.write:
        s = registry["summary"]
        print(
            f"[dry-run] registry.json — datasets {s['datasets']}, "
            f"marts {s['marts']}, signals {s['signals']}"
        )
        print("Usa --write per scrivere il file.")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / "registry.json"
    out_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"scritto {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
