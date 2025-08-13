#!/usr/bin/env bash
# Launch the Bad‑Kitty vision pipeline on the Raspberry Pi.
# Usage: ./scripts/run_on_pi.sh
# Optional env vars:
#   BK_PROJECT_DIR=/home/pi/bad-kitty
#   BK_VENV=/home/pi/bk-venv
#   BK_DEVICE_CFG=configs/device.yaml
#   BK_THRESH_CFG=configs/thresholds.yaml
#   BK_ROI=configs/roi.json
#   BK_LOG_DIR=data/events

set -euo pipefail

BK_PROJECT_DIR="${BK_PROJECT_DIR:-$HOME/bad-kitty}"
BK_VENV="${BK_VENV:-$HOME/bk-venv}"
BK_DEVICE_CFG="${BK_DEVICE_CFG:-configs/device.yaml}"
BK_THRESH_CFG="${BK_THRESH_CFG:-configs/thresholds.yaml}"
BK_ROI="${BK_ROI:-configs/roi.json}"
BK_LOG_DIR="${BK_LOG_DIR:-data/events}"

echo "[bk] project: ${BK_PROJECT_DIR}"
echo "[bk] venv:    ${BK_VENV}"
echo "[bk] configs: ${BK_DEVICE_CFG}, ${BK_THRESH_CFG}, ROI: ${BK_ROI}"
echo "[bk] logs:    ${BK_LOG_DIR}"

# Basic checks
if [[ ! -d "${BK_PROJECT_DIR}" ]]; then
  echo "[bk] ERROR: project dir not found: ${BK_PROJECT_DIR}" >&2
  exit 1
fi
cd "${BK_PROJECT_DIR}"

if [[ ! -d "${BK_VENV}" ]]; then
  echo "[bk] ERROR: venv not found at ${BK_VENV}. Create it and install deps." >&2
  exit 1
fi

# Activate venv
# shellcheck source=/dev/null
source "${BK_VENV}/bin/activate"

# Ensure log dir exists
mkdir -p "${BK_LOG_DIR}"

# Helpful: expose project on PYTHONPATH for `-m` imports
export PYTHONPATH="${BK_PROJECT_DIR}:${PYTHONPATH:-}"

# Nicer run inside tmux if available
if command -v tmux >/dev/null 2>&1 && [[ -z "${BK_NO_TMUX:-}" ]]; then
  SESSION="bk"
  if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
    tmux new -ds "${SESSION}"
  fi
  echo "[bk] attaching to tmux session '${SESSION}'"
  tmux send-keys -t "${SESSION}" "source ${BK_VENV}/bin/activate && cd ${BK_PROJECT_DIR} && python -m src.vision.pipeline --device ${BK_DEVICE_CFG} --thresholds ${BK_THRESH_CFG} --roi ${BK_ROI} --log_dir ${BK_LOG_DIR}" C-m
  tmux attach -t "${SESSION}"
  exit 0
fi

# Fallback: run in this shell
python -m src.vision.pipeline \
  --device "${BK_DEVICE_CFG}" \
  --thresholds "${BK_THRESH_CFG}" \
  --roi "${BK_ROI}" \
  --log_dir "${BK_LOG_DIR}"
