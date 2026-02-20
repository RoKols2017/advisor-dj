#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${1:-/srv/advisor}"
INBOX_ROOT="${BASE_DIR}/inbox"
INGEST_ROOT="${BASE_DIR}/ingest"

mkdir -p \
    "${INBOX_ROOT}/dc/incoming" \
    "${INBOX_ROOT}/print1/incoming" \
    "${INBOX_ROOT}/print2/incoming" \
    "${INBOX_ROOT}/_failed" \
    "${INBOX_ROOT}/_archive" \
    "${INGEST_ROOT}/logs" \
    "${INGEST_ROOT}/state" \
    "${BASE_DIR}/watch"

chmod 0750 "${BASE_DIR}" "${INBOX_ROOT}" "${INGEST_ROOT}"
chmod 0770 \
    "${INBOX_ROOT}/dc/incoming" \
    "${INBOX_ROOT}/print1/incoming" \
    "${INBOX_ROOT}/print2/incoming"
chmod 0750 "${INBOX_ROOT}/_failed" "${INBOX_ROOT}/_archive" "${INGEST_ROOT}/logs" "${INGEST_ROOT}/state" "${BASE_DIR}/watch"

printf 'Transit directories created under %s\n' "${BASE_DIR}"
