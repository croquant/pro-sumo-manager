> **_NOTE:_** These instructions are intended for AI agents

## Development

- Python dependencies are in `requirements.txt`.
- Use `.env.example` as a reference for required environment variables.
- Linting and formatting are enforced by **Ruff** (`ruff.toml`).
- `pre-commit` runs Ruff, Django system checks, migration checks, and the test suite.

## Testing & Coverage

- Always use `./test.sh` to run tests and check code coverage.
- The coverage report is generated at `coverage/coverage.json`.
- Review the coverage report to ensure your changes maintain or improve test coverage.

## Pre-commit & Coverage Notes

`pre-commit` enforces formatting, linting, and coverage tracking.

1. Run `pre-commit run --files <paths>` or `git commit` to trigger the hooks.
2. If the hooks update `.coverage_total`, stage and commit that file:
   ```bash
   git add .coverage_total
   git commit -m "<your message>"
   ```
3. When `ruff format` or `ruff --fix` rewrites files, stage the changes and rerun `pre-commit` until it passes.
4. Avoid `--no-verify` except in emergencies so coverage remains in sync with the code.
