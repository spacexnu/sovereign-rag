# Testing

Run tests through the dev container:

```bash
make test
```

If Ollama is already bound to port `11434` and Compose tries to start it, run pytest without dependencies:

```bash
docker compose run --rm --no-deps app-dev pytest -q
```

Run formatting:

```bash
make format
```

Local syntax validation can be done with Python 3.12:

```bash
python -m compileall src tests
```

The test suite covers ingest helpers, HTML report rendering, query orchestration, and changed-file filtering.
