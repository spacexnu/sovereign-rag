.PHONY: help build up down logs pull-model list-models ingest query shell dev-shell format test

COMPOSE ?= docker compose
HOST_BIN_PATH ?= /opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
MODEL ?= mistral:7b-instruct
PDF_DIR ?= ./raw_pdfs
DOCS_DIR ?= $(PDF_DIR)
QUERY_PATH ?=
EXT ?=
OLLAMA_URL ?= http://ollama:11434
NUM_CTX ?=
ifeq ($(QUERY_PATH),)
ifeq ($(origin PATH),command line)
QUERY_PATH := $(PATH)
endif
endif
EXT_ARG := $(if $(EXT),--extension $(EXT),)
NUM_CTX_ARG := $(if $(NUM_CTX),--num-ctx $(NUM_CTX),)
QUERY_VOLUME_ARG := $(if $(filter /%,$(QUERY_PATH)),--volume $(QUERY_PATH):$(QUERY_PATH):ro,)

help:
	@printf "Targets:\n"
	@printf "  build        Build Docker images\n"
	@printf "  up           Start Ollama service\n"
	@printf "  down         Stop services\n"
	@printf "  logs         Follow Ollama logs\n"
	@printf "  pull-model   Pull MODEL in Ollama (MODEL=...)\n"
	@printf "  list-models  List Ollama models\n"
	@printf "  ingest       Ingest .pdf/.md docs (DOCS_DIR=..., MODEL=...)\n"
	@printf "  query        Run analysis (QUERY_PATH=..., EXT=..., MODEL=...)\n"
	@printf "  shell        Open app shell\n"
	@printf "  dev-shell    Open app-dev shell\n"
	@printf "  format       Run ruff format in app-dev\n"
	@printf "  test         Run pytest in app-dev\n"

build:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) build

up:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) up -d ollama

down:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) down

logs:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) logs -f ollama

pull-model:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) exec ollama ollama pull $(MODEL)

list-models:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) exec ollama ollama list

ingest:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) run --rm app env PYTHONPATH=src python -m sovereign_rag.cli ingest --docs-dir $(DOCS_DIR) --model $(MODEL)

query:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) run --rm $(QUERY_VOLUME_ARG) app env PYTHONPATH=src python -m sovereign_rag.cli query --path $(QUERY_PATH) $(EXT_ARG) --model $(MODEL) --ollama-url $(OLLAMA_URL) $(NUM_CTX_ARG)

shell:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) run --rm app bash

dev-shell:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) run --rm app-dev bash

format:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) run --rm app-dev ruff format .

test:
	/usr/bin/env PATH="$(HOST_BIN_PATH)" $(COMPOSE) run --rm app-dev pytest -q
