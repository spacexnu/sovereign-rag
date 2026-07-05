# Makefile Reference

The Makefile is the recommended interface for Docker usage.

| Target | Purpose |
| --- | --- |
| `make build` | Build Docker images. |
| `make up` | Start the Ollama service. |
| `make down` | Stop services. |
| `make logs` | Follow Ollama logs. |
| `make pull-model MODEL=...` | Pull a model inside the Ollama container. |
| `make list-models` | List Ollama models. |
| `make ingest DOCS_DIR=... MODEL=...` | Index reference documents. |
| `make query QUERY_PATH=... EXT=... MODEL=...` | Analyze source code. |
| `make shell` | Open the runtime app shell. |
| `make dev-shell` | Open the dev container shell. |
| `make format` | Run Ruff format in the dev container. |
| `make test` | Run pytest in the dev container. |

## Query Variables

| Variable | Description |
| --- | --- |
| `QUERY_PATH` | File or directory to analyze. |
| `EXT` | File extension filter for directories. |
| `MODEL` | Ollama model. |
| `OLLAMA_URL` | Ollama API URL inside Docker. |
| `NUM_CTX` | Ollama context window. |
| `CHANGED_ONLY` | Set to `1` to analyze changed files only. |
| `CHANGED_BASE` | Git base ref for changed-file analysis. |
| `STAGED` | Set to `1` to analyze staged files only. |
