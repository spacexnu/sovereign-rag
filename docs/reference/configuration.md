# Configuration

Most configuration is passed through Makefile variables or CLI flags.

## Paths

| Host path | Container path | Purpose |
| --- | --- | --- |
| `./chroma_db` | `/app/chroma_db` | Persistent ChromaDB data. |
| `./output` | `/app/output` | Generated HTML reports. |
| `./raw_pdfs` | `/app/raw_pdfs` | Default reference document directory. |
| `./sources` | `/app/sources` | Optional source/reference mount. |
| `./sample_data` | `/app/sample_data` | Sample files. |

## Models

The project uses two model categories:

- SentenceTransformer embeddings for ingest, defaulting to `all-MiniLM-L6-v2`.
- Ollama LLMs for code analysis, defaulting to `mistral:7b-instruct` in the CLI and `MODEL` in the Makefile.

## Generated Data

These directories are intentionally ignored by Git:

- `chroma_db/`
- `output/`
- `site/`
- `sources/*`
