# CLI Reference

SovereignRAG exposes a unified CLI:

```bash
PYTHONPATH=src python -m sovereign_rag.cli --help
```

## ingest

```bash
PYTHONPATH=src python -m sovereign_rag.cli ingest [options]
```

| Option | Default | Description |
| --- | --- | --- |
| `--docs-dir`, `--pdf-dir` | `./raw_pdfs/` | Directory containing `.pdf` and `.md` references. `--pdf-dir` is a deprecated alias. |
| `--model` | `all-MiniLM-L6-v2` | SentenceTransformer model used for embeddings. |
| `--chunk-size-chars` | `1800` | Target chunk size in characters. |
| `--overlap-sents` | `2` | Sentence overlap between adjacent chunks. |
| `--embed-batch-size` | `32` | Embedding batch size. |

## query

```bash
PYTHONPATH=src python -m sovereign_rag.cli query [options]
```

| Option | Default | Description |
| --- | --- | --- |
| `--path`, `-p` | required | File or directory to analyze. |
| `--extension`, `-e` | none | File extension filter when `--path` is a directory. |
| `--model`, `-m` | `mistral:7b-instruct` | Ollama model used for analysis. |
| `--ollama-url` | `http://localhost:11434` | Ollama API URL. |
| `--num-ctx` | model default | Ollama context window. |
| `--changed-only` | off | Analyze only Git-changed files. |
| `--changed-base` | `HEAD` | Base ref for `--changed-only`. |
| `--staged` | off | Analyze staged files only. |
