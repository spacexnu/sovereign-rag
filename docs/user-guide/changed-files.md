# Changed Files

SovereignRAG can analyze only files changed in Git. This is useful when full-codebase review is too slow for commit or push workflows.

## Working Tree Changes

```bash
make query QUERY_PATH=./src EXT=py CHANGED_ONLY=1 MODEL=qwen2.5-coder:7b-instruct
```

By default this compares against `HEAD` and includes untracked files.

## Pre-Commit

Analyze only staged Python files:

```bash
#!/bin/sh
make query QUERY_PATH=./src EXT=py STAGED=1 MODEL=qwen2.5-coder:7b-instruct
```

Save that as `.git/hooks/pre-commit` and make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

## Pre-Push

Analyze files changed against a remote base:

```bash
#!/bin/sh
make query QUERY_PATH=./src EXT=py CHANGED_ONLY=1 CHANGED_BASE=origin/master MODEL=qwen2.5-coder:7b-instruct
```

Use `origin/main` instead if your default branch is `main`.

## Docker Note

Changed-file analysis runs on the same runtime `app` service as a full analysis —
it does **not** pull in the development image. Because Git must diff the host's
working tree (including uncommitted and untracked files), the Makefile bind-mounts
the repository at `/app` (`--volume $(CURDIR):/app`) only for `CHANGED_ONLY`/`STAGED`
runs. A full analysis keeps the service's baked-in source and selective mounts.

Detection shells out to `git` **inside the container**, so the image must contain
Git (installed via the `Dockerfile`). After pulling changes that touch the
`Dockerfile`, rebuild so Git is present:

```bash
make build
```

Bind-mounted repositories carry the host owner (typically uid 1000) while the
container runs as root, which normally makes Git reject them as *dubious
ownership*. SovereignRAG handles this itself: every Git command it runs is scoped
with a per-invocation `-c safe.directory=*`, so it trusts whatever repository it is
pointed at without any global config or `make`-time setup.

## Analyzing an external project

SovereignRAG can validate a project outside this repository. Pass an **absolute**
`QUERY_PATH`; the Makefile mounts it read-only into the container at the same path.
Changed-file mode works there too, because Git detection trusts the mounted repo:

```bash
make query QUERY_PATH=/abs/path/to/other-project EXT=py CHANGED_ONLY=1 MODEL=qwen2.5-coder:7b-instruct
```

A **relative** `QUERY_PATH` (e.g. `../other-project`) is *not* mounted and will not
be found inside the container — always use an absolute path for external projects.
