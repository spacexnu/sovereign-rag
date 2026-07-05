# Quickstart

This flow builds the images, starts Ollama, indexes security references, and analyzes Python files.

## 1. Build And Start

```bash
make build
make up
make pull-model MODEL=qwen2.5:3b-instruct
```

## 2. Add Reference Documents

Put `.pdf` or `.md` security references under `raw_pdfs/` or another local directory.

```bash
make ingest DOCS_DIR=./raw_pdfs MODEL=all-MiniLM-L6-v2
```

The ingest step writes vectors into `./chroma_db`.

## 3. Analyze Code

Analyze a single file:

```bash
make query QUERY_PATH=./src/sovereign_rag/query.py MODEL=qwen2.5:3b-instruct
```

Analyze a directory by extension:

```bash
make query QUERY_PATH=./src EXT=py MODEL=qwen2.5:3b-instruct
```

Reports are written under `output/<timestamp>/report.html`.

## 4. Stop Services

```bash
make down
```
