#!/usr/bin/env bash
# Sync the local repo to your Raspberry Pi using rsync.
# This version auto-starts ssh-agent (if needed) and loads your key so you only
# enter the passphrase once per login session.
#
# Override via env vars if you like:
#   PI_HOST=bad-kitty@bad-kitty.local
#   PI_DIR=/home/bad-kitty/bad-kitty
#   PI_SSH_KEY=~/.ssh/id_rsa
#   EXCLUDE=".venv .git __pycache__ data/events *.mp4 *.jpg"
#   RSYNC_EXTRA="--dry-run"

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"


PI_USER="bad-kitty"
PI_HOST="${PI_HOST:-bad-kitty@bad-kitty.local}"
PI_DIR="${PI_DIR:-/home/bad-kitty/main}"
PI_SSH_KEY="${PI_SSH_KEY:-$HOME/.ssh/id_rsa}"
EXCLUDE_LIST=(${EXCLUDE:-.bk-venv .git __pycache__ data/events *.mp4 *.jpg})
RSYNC_EXTRA="${RSYNC_EXTRA:-}"

# ---------------------------
# SSH agent + key management
# ---------------------------
ensure_ssh_agent() {
  if [[ -z "${SSH_AUTH_SOCK:-}" ]]; then
    echo "[bk] starting ssh-agent"
    eval "$(ssh-agent -s)" >/dev/null
  fi
}

key_is_loaded() {
  # Return 0 if PI_SSH_KEY fingerprint is present in ssh-agent, else 1.
  [[ -f "$PI_SSH_KEY" ]] || return 1
  local fp pub_fp
  fp="$(ssh-keygen -lf "$PI_SSH_KEY" 2>/dev/null | awk '{print $2}')" || return 1
  # ssh-add -l prints loaded key fingerprints in SHA256 by default
  if ssh-add -l >/dev/null 2>&1; then
    ssh-add -l | awk '{print $2}' | grep -q "$fp" && return 0
  fi
  return 1
}

load_key_if_needed() {
  [[ -f "$PI_SSH_KEY" ]] || { echo "[bk] note: key $PI_SSH_KEY not found; using SSH defaults"; return; }
  if key_is_loaded; then
    echo "[bk] ssh key already loaded: $PI_SSH_KEY"
    return
  fi

  echo "[bk] loading ssh key into agent: $PI_SSH_KEY"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    # macOS: store in Keychain so it persists across reboots
    if ssh-add --apple-use-keychain "$PI_SSH_KEY"; then
      echo "[bk] key added to agent + Keychain (macOS)."
      return
    fi
  fi

  # Generic path (Linux/macOS without Keychain flag)
  ssh-add "$PI_SSH_KEY"
  echo "[bk] key added to agent."
}

ensure_ssh_agent
load_key_if_needed

# ---------------------------
# SSH / rsync settings
# ---------------------------
SSH_OPTS="-o StrictHostKeyChecking=accept-new"
if [[ -f "$PI_SSH_KEY" ]]; then
  SSH_OPTS="$SSH_OPTS -i $PI_SSH_KEY"
fi
RSYNC_RSH="ssh $SSH_OPTS"

echo "[bk] syncing to ${PI_HOST}:${PI_DIR}"

# Build exclude args
EXCLUDES=()
for item in "${EXCLUDE_LIST[@]}"; do
  EXCLUDES+=(--exclude "$item")
done

# Ensure remote directory exists (allow interactive auth if agent not available)
ssh ${SSH_OPTS} "${PI_HOST}" "mkdir -p '${PI_DIR}' ; echo 'cwd: ${PWD}'"


# Sync
rsync -avz --delete "${EXCLUDES[@]}" ${RSYNC_EXTRA} -e "${RSYNC_RSH}" ./ "${PI_HOST}:${PI_DIR}"

echo "[bk] synced project files to bad-kitty@bad-kitty.local."
echo "[bk] downloading missing dependencies..."

# Install requirements on Pi
ssh $PI_HOST <<'EOF'
source ~/main/.bk-venv/bin/activate
cd main
python -m pip install --upgrade pip
python -m pip install -r ~/main/requirements.txt
EOF

echo "[bk] project dependencies installed."
echo "[bk] done."

