.PHONY: help build up down logs pull-model list-models ingest query shell dev-shell format test

COMPOSE ?= docker compose
MODEL ?= mistral:7b-instruct
PDF_DIR ?= ./raw_pdfs
PATH ?=
EXT ?=
OLLAMA_URL ?= http://ollama:11434
EXT_ARG := $(if $(EXT),--extension $(EXT),)

help:
	@printf "Targets:\n"
	@printf "  build        Build Docker images\n"
	@printf "  up           Start Ollama service\n"
	@printf "  down         Stop services\n"
	@printf "  logs         Follow Ollama logs\n"
	@printf "  pull-model   Pull MODEL in Ollama (MODEL=...)\n"
	@printf "  list-models  List Ollama models\n"
	@printf "  ingest       Ingest PDFs (PDF_DIR=..., MODEL=...)\n"
	@printf "  query        Run analysis (PATH=..., EXT=..., MODEL=...)\n"
	@printf "  shell        Open app shell\n"
	@printf "  dev-shell    Open app-dev shell\n"
	@printf "  format       Run ruff format in app-dev\n"
	@printf "  test         Run pytest in app-dev\n"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d ollama

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f ollama

pull-model:
	$(COMPOSE) exec ollama ollama pull $(MODEL)

list-models:
	$(COMPOSE) exec ollama ollama list

ingest:
	$(COMPOSE) run --rm app python src/cli.py ingest --pdf-dir $(PDF_DIR) --model $(MODEL)

query:
	$(COMPOSE) run --rm app python src/cli.py query --path $(PATH) $(EXT_ARG) --model $(MODEL) --ollama-url $(OLLAMA_URL)

shell:
	$(COMPOSE) run --rm app bash

dev-shell:
	$(COMPOSE) run --rm app-dev bash

format:
	$(COMPOSE) run --rm app-dev ruff format .

test:
	$(COMPOSE) run --rm app-dev pytest -q
