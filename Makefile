PYTHON ?= python3
# toolkit CLI: safe_connect (lab-connectors) applica già memory_limit=2GB —
# nessun wrapper duckdb necessario (decisione cross-repo, vedi open-conto-annuale).
TOOLKIT = $(PYTHON) -m toolkit.cli.app

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
	toolkit registry build

registry-write:
	toolkit registry build --write

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
