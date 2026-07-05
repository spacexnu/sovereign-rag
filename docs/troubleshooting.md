# Troubleshooting

Common failures and how to fix them.

## `address already in use` on port 11434

```
Error response from daemon: failed to set up container networking: driver failed
programming external connectivity on endpoint sovereign-ollama ... failed to bind
host port 0.0.0.0:11434/tcp: address already in use
```

**Cause:** an Ollama is already running on the host (e.g. a native/systemd
install) holding port `11434`, so the compose `ollama` service can't bind the
same port.

**Fix:** reuse the host Ollama instead of starting the compose service by adding
`HOST_OLLAMA=1`:

```bash
make query QUERY_PATH=/abs/path EXT=py CHANGED_ONLY=1 MODEL=qwen2.5-coder:7b HOST_OLLAMA=1
```

This passes `--no-deps` (skips the compose `ollama` service) and points
`OLLAMA_URL` at `http://host.docker.internal:11434`.

!!! warning "It's `HOST_OLLAMA`, not `OLLAMA_HOST`"
    `HOST_OLLAMA=1` is the Makefile switch to *use the host's Ollama*.
    `OLLAMA_HOST` is Ollama's own environment variable for its bind address (see
    below). Passing `OLLAMA_HOST=1` to `make` does nothing and you'll fall back
    to the port conflict above.

Alternatively, stop the native Ollama and let the compose service own port
`11434` — but you lose the models you already pulled natively.

## `Failed to connect to Ollama` with `HOST_OLLAMA=1`

```
Error processing ...: Failed to connect to Ollama. Please check that Ollama is
downloaded, running and accessible. https://ollama.com/download
```

The URL now resolves (`http://host.docker.internal:11434`) but the container
can't reach the host Ollama.

**Cause:** on Linux/WSL2 a native Ollama binds `127.0.0.1:11434` by default. The
container reaches the host via the gateway IP, so a loopback-only listener
refuses the connection. Check with:

```bash
ss -tlnp | grep 11434
```

If it shows `127.0.0.1:11434` instead of `0.0.0.0:11434`, that's the problem.

**Fix (systemd install):** add a drop-in so Ollama listens on all interfaces,
then restart it:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\n' \
  | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Confirm it now listens on `0.0.0.0:11434`:

```bash
ss -tlnp | grep 11434
```

**Fix (manual `ollama serve`):** start it with the env var set:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

!!! note "`host.docker.internal` on Linux"
    The `app` service maps `host.docker.internal` to `host-gateway` via
    `extra_hosts` in `docker-compose.yml`, so the name resolves on Linux. The
    only remaining requirement is that the host Ollama listens on `0.0.0.0`.

## Citations show `unknown source`

Chunks ingested before source-metadata support lack a `source` in their
metadata and fall back to `unknown source` in reports.

**Fix:** re-ingest your reference documents so each chunk gets a `source`
metadata entry:

```bash
make ingest DOCS_DIR=./raw_pdfs MODEL=all-MiniLM-L6-v2
```

## Retrieval returns irrelevant or empty context

**Cause:** the embedding model used at ingest time doesn't match the one used at
query time. Query's embedding model is hardcoded to
`sentence-transformers/all-MiniLM-L6-v2`; if you ingested with a different
SentenceTransformer, the embeddings aren't comparable.

**Fix:** always ingest with `all-MiniLM-L6-v2` (the default) and re-ingest if you
previously used something else. Note `--model` means different things per
command: for `ingest` it's the SentenceTransformer; for `query` it's the Ollama
LLM.

## Ollama falls back to CPU / runs out of VRAM

Large source files inflate the prompt (whole file + retrieved context), which
can blow past GPU VRAM and force partial CPU offload.

**Fix:** cap the context window so the KV cache fits in VRAM:

```bash
make query QUERY_PATH=./src EXT=py MODEL=qwen2.5-coder:7b NUM_CTX=8192
```

Verify the model is fully on GPU with `ollama ps` (look for `100% GPU`).

## `QUERY_PATH` seems ignored

The Makefile reads the path from `QUERY_PATH`. If you pass the reserved make
variable `PATH=` on the command line it's picked up as a fallback, but this is
fragile and pollutes the executable search path — prefer `QUERY_PATH`.
