# Ingest References

The ingest command indexes security documents into ChromaDB. Supported source formats are:

- `.pdf`
- `.md`

Markdown syntax is reduced to prose before sentence segmentation. PDF text is extracted with PyMuPDF. Both formats are cleaned, split into relevant sentence chunks, embedded, and stored with source metadata.

## Command

```bash
make ingest DOCS_DIR=./raw_pdfs MODEL=all-MiniLM-L6-v2
```

Equivalent CLI:

```bash
PYTHONPATH=src python -m sovereign_rag.cli ingest \
  --docs-dir ./raw_pdfs \
  --model all-MiniLM-L6-v2
```

## Tuning

```bash
PYTHONPATH=src python -m sovereign_rag.cli ingest \
  --docs-dir ./raw_pdfs \
  --chunk-size-chars 1800 \
  --overlap-sents 2 \
  --embed-batch-size 32
```

Use larger chunks when you want fewer retrieval blocks with more context. Use smaller chunks when source documents are dense and findings need tighter citations.

## Persistence

The vector database is stored in:

```text
./chroma_db
```

The Docker Compose app mounts it into the container at `/app/chroma_db`.
