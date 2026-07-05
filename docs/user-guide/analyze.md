# Analyze Code

The query command reviews source files using the indexed security references.

## Single File

```bash
make query QUERY_PATH=./src/sovereign_rag/query.py MODEL=qwen2.5:3b-instruct
```

## Directory

Directories require an extension filter:

```bash
make query QUERY_PATH=./src EXT=py MODEL=qwen2.5:3b-instruct
```

## Context Window

Use `NUM_CTX` when a model needs a smaller or larger Ollama context window:

```bash
make query QUERY_PATH=./src EXT=py MODEL=qwen2.5-coder:7b-instruct NUM_CTX=8192
```

Lower values can reduce VRAM pressure. Higher values allow larger code and retrieved reference context.

## External Source Trees

Absolute `QUERY_PATH` values are mounted read-only into the app container at the same path:

```bash
make query QUERY_PATH=/path/to/other/project EXT=py MODEL=qwen2.5:3b-instruct
```
