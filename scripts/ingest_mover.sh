#!/usr/bin/env bash
set -euo pipefail

INBOX_ROOT="${INBOX_ROOT:-/srv/advisor/inbox}"
WATCH_DIR="${WATCH_DIR:-/var/lib/docker/volumes/advisor-dj_data/_data/watch}"
FAILED_DIR="${FAILED_DIR:-${INBOX_ROOT}/_failed}"
ARCHIVE_DIR="${ARCHIVE_DIR:-${INBOX_ROOT}/_archive}"
STATE_DIR="${STATE_DIR:-/srv/advisor/ingest/state}"
LOG_FILE="${LOG_FILE:-/srv/advisor/ingest/logs/ingest_mover.log}"
LOCK_FILE="${LOCK_FILE:-/var/lock/advisor-ingest.lock}"
SEEN_DB="${SEEN_DB:-${STATE_DIR}/seen_files.db}"
MIN_AGE_SECONDS="${MIN_AGE_SECONDS:-20}"
MAX_FILES_PER_RUN="${MAX_FILES_PER_RUN:-500}"
SOURCES="${SOURCES:-dc print1 print2}"

mkdir -p "${WATCH_DIR}" "${FAILED_DIR}" "${ARCHIVE_DIR}" "${STATE_DIR}" "$(dirname "${LOG_FILE}")" "$(dirname "${LOCK_FILE}")"
touch "${SEEN_DB}" "${LOG_FILE}"

exec 200>"${LOCK_FILE}"
if ! flock -n 200; then
    exit 0
fi

log() {
    printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" >>"${LOG_FILE}"
}

safe_move() {
    local source_file="$1"
    local target_file="$2"
    local target_dir
    local target_name
    local target_ext

    target_dir="$(dirname "${target_file}")"
    target_name="$(basename "${target_file}")"
    target_ext=""

    mkdir -p "${target_dir}"

    if [[ -e "${target_file}" ]]; then
        if [[ "${target_name}" == *.* ]]; then
            target_ext=".${target_name##*.}"
            target_name="${target_name%.*}"
        fi
        target_file="${target_dir}/${target_name}-$(date +%s)${target_ext}"
    fi

    mv "${source_file}" "${target_file}"
}

is_file_stable() {
    local file_path="$1"
    local size_before
    local size_after
    local mtime
    local now

    size_before="$(stat -c '%s' "${file_path}")"
    mtime="$(stat -c '%Y' "${file_path}")"
    now="$(date +%s)"

    if (( now - mtime < MIN_AGE_SECONDS )); then
        return 1
    fi

    sleep 1
    size_after="$(stat -c '%s' "${file_path}")"
    [[ "${size_before}" == "${size_after}" ]]
}

record_seen() {
    local record="$1"
    printf '%s\n' "${record}" >>"${SEEN_DB}"
}

was_seen() {
    local record="$1"
    grep -Fxq "${record}" "${SEEN_DB}"
}

process_file() {
    local source_name="$1"
    local file_path="$2"
    local base_name
    local extension
    local file_size
    local file_hash
    local dedup_key
    local watch_target
    local tmp_target
    local archive_target

    base_name="$(basename "${file_path}")"
    extension="${base_name##*.}"

    if [[ "${extension}" != "csv" && "${extension}" != "json" ]]; then
        return 0
    fi

    if ! is_file_stable "${file_path}"; then
        log "source=${source_name} file=${base_name} status=skip reason=unstable"
        return 0
    fi

    file_size="$(stat -c '%s' "${file_path}")"
    file_hash="$(sha256sum "${file_path}" | cut -d' ' -f1)"
    dedup_key="${source_name}|${base_name}|${file_size}|${file_hash}"

    if was_seen "${dedup_key}"; then
        archive_target="${ARCHIVE_DIR}/${source_name}/duplicates/${base_name}"
        safe_move "${file_path}" "${archive_target}"
        log "source=${source_name} file=${base_name} status=skip reason=duplicate"
        return 0
    fi

    watch_target="${WATCH_DIR}/${source_name}__${base_name}"
    tmp_target="${WATCH_DIR}/.${source_name}__${base_name}.part"
    cp --preserve=timestamps "${file_path}" "${tmp_target}"
    mv "${tmp_target}" "${watch_target}"

    archive_target="${ARCHIVE_DIR}/${source_name}/$(date -u +%Y-%m-%d)/${base_name}"
    safe_move "${file_path}" "${archive_target}"
    record_seen "${dedup_key}"
    log "source=${source_name} file=${base_name} status=queued watch_file=$(basename "${watch_target}")"
}

main() {
    local source_name
    local source_dir
    local processed_count=0

    for source_name in ${SOURCES}; do
        source_dir="${INBOX_ROOT}/${source_name}/incoming"
        if [[ ! -d "${source_dir}" ]]; then
            log "source=${source_name} status=skip reason=missing_dir path=${source_dir}"
            continue
        fi

        while IFS= read -r -d '' file_path; do
            if (( processed_count >= MAX_FILES_PER_RUN )); then
                log "status=stop reason=max_files_per_run limit=${MAX_FILES_PER_RUN}"
                return 0
            fi

            if process_file "${source_name}" "${file_path}"; then
                processed_count=$((processed_count + 1))
            else
                safe_move "${file_path}" "${FAILED_DIR}/${source_name}/$(basename "${file_path}")"
                log "source=${source_name} file=$(basename "${file_path}") status=failed reason=process_error"
            fi
        done < <(find "${source_dir}" -maxdepth 1 -type f \( -name '*.csv' -o -name '*.json' \) -print0)
    done

    log "status=done processed=${processed_count}"
}

main "$@"
