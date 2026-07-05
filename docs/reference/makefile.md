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
| `HOST_OLLAMA` | Set to `1` to use an Ollama running on the host instead of the compose service. |

## Using a host Ollama (`HOST_OLLAMA=1`)

If you already run Ollama natively on the host, starting the compose `ollama`
service too fails with `address already in use` on port `11434`. Set
`HOST_OLLAMA=1` to skip the compose service and talk to the host instead:

```bash
make query QUERY_PATH=/abs/path EXT=py CHANGED_ONLY=1 HOST_OLLAMA=1 MODEL=qwen2.5-coder:7b-instruct
```

This passes `--no-deps` and points `OLLAMA_URL` at `http://host.docker.internal:11434`
(reachable via the `app` service's `extra_hosts` entry). The host Ollama must listen
on all interfaces, not just localhost — start it with `OLLAMA_HOST=0.0.0.0:11434`
(a native install bound to `127.0.0.1` will refuse the container's connection).
