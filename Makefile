PYTHON ?= python3
# scripts/run_toolkit.py: wrapper che monkey-patcha duckdb.connect() per
# impostare memory_limit, threads e preserve_insertion_order — evita OOM
# su runner CI con RAM limitata (i parquet RNA ~100MB/anno per anno).
TOOLKIT = $(PYTHON) scripts/run_toolkit.py

# --- Dataset principali ---

.PHONY: run-aiuti run-misure run-all
run-aiuti:
	$(TOOLKIT) run --config datasets/rna-aiuti-stato/dataset.yml

run-misure:
	$(TOOLKIT) run --config datasets/rna-misure/dataset.yml

run-all: run-aiuti run-misure

# --- Validazione config ---

.PHONY: check
check:
	@for f in $$(find datasets -name dataset.yml | sort); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Pulizia ---

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/probe out/data/raw out/data/clean out/data/mart out/data/cross .tmp/

.PHONY: clean-runs
clean-runs:
	rm -rf out/data/_runs/

# --- Registry (artifact catalogo — dry-run di default) ---

.PHONY: registry registry-write
registry:
	$(PYTHON) scripts/build_registry.py

registry-write:
	$(PYTHON) scripts/build_registry.py --write

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
