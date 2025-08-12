> **_NOTE:_** These instructions are intended for AI agents

## Pre-commit & Coverage Notes

`pre-commit` enforces formatting, linting, and static typing.

1. Run `pre-commit run --files <paths>` or `git commit` to trigger the hooks.
2. When `ruff format` or `ruff --fix` rewrites files, stage the changes and rerun `pre-commit` until it passes.
3. Avoid `--no-verify` except in emergencies so coverage remains in sync with the code.
