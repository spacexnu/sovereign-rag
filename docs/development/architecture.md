# Architecture

The code is split into a small set of modules:

```text
src/sovereign_rag/
├── cli.py          # unified ingest/query command
├── ingest.py       # PDF/Markdown preprocessing and ChromaDB indexing
├── query.py        # retrieval, Ollama analysis, changed-file filtering
└── html_report.py  # report rendering
```

## Ingest Flow

```mermaid
flowchart LR
    A[PDF/Markdown files] --> B[clean_text / strip_markdown]
    B --> C[spaCy sentence segmentation]
    C --> D[relevance filter]
    D --> E[chunk builder]
    E --> F[SentenceTransformer embeddings]
    F --> G[ChromaDB security_docs collection]
```

## Query Flow

```mermaid
flowchart LR
    A[Path or directory] --> B[extension filter]
    B --> C{changed only?}
    C -->|yes| D[Git diff/staged filter]
    C -->|no| E[file list]
    D --> E
    E --> F[retrieve top 3 chunks]
    F --> G[Ollama prompt]
    G --> H[HTML report]
```

## Design Notes

- The vector collection is named `security_docs`.
- Retrieved chunks carry `source` metadata so findings can cite reference documents.
- Query reports are generated after all selected files are processed.
- Changed-file mode is implemented before model initialization so no-op hooks return quickly.
