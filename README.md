# SovereignRAG

**Sovereign Retrieval Augmented Generation for Secure Code Analysis**

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Build](https://github.com/spacexnu/sovereign-rag/actions/workflows/build.yml/badge.svg)](https://github.com/spacexnu/sovereign-rag/actions/workflows/build.yml)

---

🚀 Open-source sovereign RAG engine for security code auditing.

- 100% offline
- Runs on personal hardware (Apple M1 fully supported)
- Uses LLMs like phi3, mistral, codellama via Ollama
- Vector DB via ChromaDB
- Preprocessing with spaCy for efficient semantic chunking
- BSD 3-Clause License

---

<img alt="graph" height="50%" src="sovereign-rag.png" width="50%"/>


## Philosophy

Sovereign AI - private, secure, under full control.

This project is part of a broader experiment applying sovereign AI pipelines for security code analysis.
It's a fully private, offline, sovereign AI pipeline for security code auditing. 
Free from cloud lock-in, vendor tracking or corporate surveillance.

Build your own lab. Own your models. Control your data.


---

## Install

Requirements:

- Python 3.10+
- Ollama
- PyMuPDF
- spaCy
- sentence-transformers
- chromadb
- llama-index and related packages (llama-index-llms-ollama, llama-index-vector-stores-chroma, llama-index-embeddings-huggingface)
- colorama (for colored CLI output)

Install dependencies:

```bash
pip install -r requirements/requirements.txt
python -m spacy download en_core_web_sm
```

For development, install additional dependencies:

```bash
pip install -r requirements/requirements_dev.txt
```

## Usage

SovereignRAG provides a unified CLI interface with colored output for better readability. There are two main commands:

### Ingest PDF Documents

To ingest security-related PDF documents into the vector database:

```bash
python src/cli.py ingest [--pdf-dir PATH_TO_PDF_DIR] [--model MODEL_NAME]
```

Options:
- `--pdf-dir`: Directory containing PDF files to index (default: ./raw_pdfs/)
- `--model`: Sentence transformer model to use (default: all-MiniLM-L6-v2)

Example:
```bash
python src/cli.py ingest --pdf-dir ./security_pdfs/ --model all-MiniLM-L6-v2
```

### Query for Security Analysis

To analyze a source code file for security vulnerabilities:

```bash
python src/cli.py query --file PATH_TO_SOURCE_FILE [--model MODEL_NAME] [--ollama-url URL]
```

Options:
- `--file` or `-f`: Path to the source code file to analyze (required)
- `--model` or `-m`: Ollama model to use (default: mistral:7b-instruct)
- `--ollama-url`: Ollama API URL (default: http://localhost:11434)

Example:
```bash
python src/cli.py query --file ./src/app.py --model mistral:7b-instruct
```

### Individual Commands

You can still use the individual scripts directly:

```bash
python src/ingest.py --pdf-dir ./security_pdfs/
python src/query.py --file ./src/app.py
```
![animated-gif-cli-running](sovereign-rag-faster.gif)

## Docker

Run the full stack (Python app, Ollama with Phi-3, and persistent ChromaDB) via Docker.

Prerequisites:

- Docker and Docker Compose

Build images and start services:

```bash
docker compose build
docker compose up -d ollama
```

Pull a model (e.g., Mistral 7B Instruct). Use exec to run inside the running service:

```bash
docker compose exec ollama ollama pull mistral:7b-instruct
```

If the service isn’t ready yet, wait a few seconds or check logs:

```bash
docker compose logs -f ollama
```

Note: If a model tag is not found (e.g., "pull model manifest: file does not exist"), try a known tag like `mistral:7b-instruct` or `phi3:mini`, or list available models:

```bash
docker compose exec ollama ollama list
```

You can also browse tags at https://ollama.com/library

Ingest PDFs (mounted at ./raw_pdfs on the host):

```bash
docker compose run --rm app python src/cli.py ingest --pdf-dir ./raw_pdfs/ --model all-MiniLM-L6-v2
```

Query code for security analysis. Note: when running inside Docker, point to the Ollama service URL.

```bash
# Single file (use --path instead of --file)
    docker compose run --rm app python src/cli.py query --path ./src/query.py --model mistral:7b-instruct --ollama-url http://ollama:11434

# Directory + extension filter
docker compose run --rm app python src/cli.py query --path ./src --extension py --model mistral:7b-instruct --ollama-url http://ollama:11434
```

Outputs and data persistence:

- ChromaDB data: `./chroma_db` (host) is mounted to `/app/chroma_db` (container)
- Reports: `./output` (host) is mounted to `/app/output` (container)
- PDFs: `./raw_pdfs` (host) is mounted to `/app/raw_pdfs` (container)

Stop services:

```bash
docker compose down
```

### Docker: Development image (requirements-dev)

Use the dev image to get `pytest`, `ruff`, and other developer tools from `requirements/requirements_dev.txt`.

Build and open a shell in the dev container:

```bash
docker compose build app-dev
docker compose run --rm app-dev bash
```

Inside the dev container, run common tasks:

```bash
# Format
ruff format .

# Lint
ruff check .

# Tests
pytest -q

# App commands (same as prod), pointing to Ollama service
python src/cli.py ingest --pdf-dir ./raw_pdfs/ --model all-MiniLM-L6-v2
python src/cli.py query --path ./src --extension py --model mistral:7b-instruct --ollama-url http://ollama:11434
```

## Development

### Code Formatting

This project uses [ruff](https://github.com/astral-sh/ruff) for code formatting. To format all Python files in the project, run:

```bash
ruff format .
```

This will automatically format your code according to the style defined in the pyproject.toml file.
