# Reports

Each successful query writes an HTML report under:

```text
output/<timestamp>/report.html
```

The report contains one collapsible section per analyzed file.

For every file, the output includes:

- The model's security analysis.
- Suggested fixes when vulnerabilities are found.
- The reference source documents retrieved from ChromaDB.

If no vulnerabilities are found, the prompt asks the model to state:

```text
No vulnerabilities detected.
```

Reports are local artifacts. The `output/` directory is ignored by Git.
