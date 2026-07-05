# Install

SovereignRAG is designed to run through Docker Compose. The Makefile wraps the Docker commands used day to day.

## Requirements

- Docker and Docker Compose
- Enough disk space for Ollama models, ChromaDB data, and generated reports
- Optional: a GPU available to Docker for faster Ollama inference

## Build Images

```bash
make build
```

Start the Ollama service:

```bash
make up
```

Pull a model:

```bash
make pull-model MODEL=qwen2.5:3b-instruct
```

## Local CLI Option

For local development only, install the package in editable mode:

```bash
pip install -e .
sovereign-rag --help
```

The Docker path is still the recommended default because it keeps runtime dependencies isolated.
