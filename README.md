# SovereignRAG

**Sovereign Retrieval Augmented Generation for Secure Code Analysis**

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Build](https://github.com/seuuser/seurepo/actions/workflows/build.yml/badge.svg)](link-pro-workflow)

---

🚀 Open-source sovereign RAG engine for security code auditing.

- 100% offline
- Runs on personal hardware (Apple M1 fully supported)
- Uses LLMs like phi3, mistral, codellama via Ollama
- Vector DB via ChromaDB
- Preprocessing with spaCy for efficient semantic chunking
- BSD 3-Clause License

---

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
- `--model` or `-m`: Ollama model to use (default: phi3:3b)
- `--ollama-url`: Ollama API URL (default: http://localhost:11434)

Example:
```bash
python src/cli.py query --file ./src/app.py --model phi3:3b
```

### Individual Commands

You can still use the individual scripts directly:

```bash
python src/ingest.py --pdf-dir ./security_pdfs/
python src/query.py --file ./src/app.py
```

## Development

### Code Formatting

This project uses [ruff](https://github.com/astral-sh/ruff) for code formatting. To format all Python files in the project, run:

```bash
ruff format .
```

This will automatically format your code according to the style defined in the pyproject.toml file.