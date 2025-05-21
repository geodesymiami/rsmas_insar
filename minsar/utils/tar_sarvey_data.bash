#!/usr/bin/env bash

set -euo pipefail

# Help message
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 1 ]]; then
  echo "Usage: $0 <directory>"
  echo
  echo "Create a tar.gz archive containing:"
  echo "  <directory>/inputs/"
  echo "  <directory>/inverted/"
  echo "  <directory>/config.json"
  echo "  <directory>/subset.log"
  echo
  echo "Example:"
  echo "  $0 milleniumtower"
  echo "  => produces milleniumtower.tar.gz"
  exit 1
fi

BASE_DIR="$1"
ARCHIVE_NAME="${BASE_DIR}.tar.gz"

# Check required files/directories
for item in "inputs" "inverted" "config.json" "subset.log"; do
  if [[ ! -e "${BASE_DIR}/${item}" ]]; then
    echo "[ERROR] Missing: ${BASE_DIR}/${item}"
    exit 2
  fi
done

# Create tar.gz archive
echo "Creating archive: ${ARCHIVE_NAME}"
tar -czf "${ARCHIVE_NAME}" -C "${BASE_DIR}" inputs inverted config.json subset.log

echo "Done."
