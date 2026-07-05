# GitHub Pages

This repository includes a MkDocs Material site that can be deployed to GitHub Pages.

## Local Build

Install docs dependencies:

```bash
pip install -r requirements/requirements_docs.txt
```

Build in strict mode:

```bash
mkdocs build --strict
```

Serve locally:

```bash
mkdocs serve
```

## Published URL

The configured site URL is:

```text
https://spacexnu.github.io/sovereign-rag/
```

## GitHub Settings

In the repository settings, configure Pages to use:

```text
Source: GitHub Actions
```

The workflow deploys only on pushes to `master`. Pull requests run a strict docs build without publishing.
