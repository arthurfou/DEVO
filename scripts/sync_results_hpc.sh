#!/usr/bin/env bash
# Rapatrie (pull) les résultats DEVO du cluster NUS vers ce repo local.
set -euo pipefail

REMOTE_HOST="xlogin_nus"
REMOTE_PATH="~/arthur_ipal/DEVO/results/"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
DEST_DIR="${SCRIPT_DIR}/../results_hpc/"

mkdir -p "${DEST_DIR}"

rsync -avz --progress --info=progress2 \
    "${REMOTE_HOST}:${REMOTE_PATH}" \
    "${DEST_DIR}"

echo "Sync terminé : résultats disponibles dans ${DEST_DIR}"
