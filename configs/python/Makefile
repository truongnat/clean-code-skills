# A small Makefile for Python: one command to check, one to fix.
# (If the repo already uses poetry/uv, move these targets into its task runner.)
PYTHON ?= python3
VENV   ?= .venv
BIN    := $(VENV)/bin
REF    := src/orders_good.py

.PHONY: setup check fix fmt type self-check

setup:
	@$(PYTHON) -m venv $(VENV)
	@$(BIN)/pip install -q --upgrade pip
	@$(BIN)/pip install -q "ruff>=0.6" "black>=24" "mypy>=1.10" pytest

check:
	@$(BIN)/ruff check .
	@$(BIN)/black --check .
	@$(BIN)/mypy $(REF)

fix:
	@$(BIN)/ruff check --fix .
	@$(BIN)/black .

fmt:
	@$(BIN)/black .

type:
	@$(BIN)/mypy $(REF)

# Dogfood: run it on the demo files to see the rules actually fire
self-check:
	@echo "-- ruff on the COMPLIANT file ($(REF)):"
	@$(BIN)/ruff check $(REF)
	@echo "-- ruff on the VIOLATING file (src/orders_bad.py):"
	@$(BIN)/ruff check src/orders_bad.py --statistics || true
