#!/usr/bin/env bash
# Sync the local repo to your Raspberry Pi using rsync.
# Usage:
#   ./scripts/sync_to_pi.sh
# Optional env vars:
#   PI_HOST=pi@badkitty.local
#   PI_DIR=/home/pi/bad-kitty
#   EXCLUDE=".venv .git __pycache__ data/events *.mp4 *.jpg"
# Pass RSYNC_EXTRA flags via env if needed (e.g., --dry-run)

set -euo pipefail

PI_HOST="${PI_HOST:-pi@badkitty.local}"
PI_DIR="${PI_DIR:-/home/pi/bad-kitty}"
EXCLUDE_LIST=(${EXCLUDE:-.venv .git __pycache__ data/events *.mp4 *.jpg})
RSYNC_EXTRA="${RSYNC_EXTRA:-}"

echo "[bk] syncing to ${PI_HOST}:${PI_DIR}"

# Build exclude args
EXCLUDES=()
for item in "${EXCLUDE_LIST[@]}"; do
  EXCLUDES+=(--exclude "$item")
done

# Ensure remote directory exists
ssh -o BatchMode=yes "${PI_HOST}" "mkdir -p '${PI_DIR}'"

# Sync
rsync -avz --delete "${EXCLUDES[@]}" ${RSYNC_EXTRA} ./ "${PI_HOST}:${PI_DIR}"

echo "[bk] done."
echo "[bk] tip: on the Pi, run: ${PI_DIR}/scripts/run_on_pi.sh"
