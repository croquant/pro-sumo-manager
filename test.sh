#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

COVERAGE_FILE="coverage/.coverage_total"

# Run tests and generate coverage
uv run coverage run manage.py test
uv run coverage json
uv run coverage report

# Extract the overall coverage percentage (can be a decimal)
TOTAL=$(uv run coverage report --format=total)

echo "Total coverage: ${TOTAL}%"

# If this is the first run, record the baseline and exit
if [[ ! -f "${COVERAGE_FILE}" ]]; then
  printf '%s\n' "${TOTAL}" > "${COVERAGE_FILE}"
  echo "Saved initial coverage percent."
  exit 0
fi

# Read previous coverage value
PREV_TOTAL=$(< "${COVERAGE_FILE}")

# Compare and act
if awk -v a="$TOTAL" -v b="$PREV_TOTAL" 'BEGIN{exit (a+0 < b+0)?0:1}'; then
  echo "Error: Coverage decreased from ${PREV_TOTAL}% to ${TOTAL}%!" >&2
  exit 1
else
  printf '%s\n' "${TOTAL}" > "${COVERAGE_FILE}"
  echo "Coverage did not decrease."
fi
