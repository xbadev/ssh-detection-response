#!/usr/bin/env bash
# ============================================================
# Phase 03 — UFW install
# ============================================================
# Configures UFW to allow SSH only from the internal lab subnet.
# Reads the subnet value from lab.env so a network change does
# not require editing this script.
#
# Usage:  sudo ./install-ufw.sh
# ============================================================

set -euo pipefail

LAB_ENV="${LAB_ENV:-/etc/ssh-detection-response/lab.env}"

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: must run as root (use sudo)." >&2
    exit 1
fi

if [[ ! -r "$LAB_ENV" ]]; then
    echo "ERROR: cannot read $LAB_ENV" >&2
    exit 2
fi

# shellcheck disable=SC1090
source "$LAB_ENV"
SUBNET="${INTERNAL_SUBNET:?INTERNAL_SUBNET not set in $LAB_ENV}"

echo "==> Resetting UFW to a known state"
ufw --force reset >/dev/null

echo "==> Default policies: deny incoming, allow outgoing"
ufw default deny incoming
ufw default allow outgoing

echo "==> Allowing SSH from internal subnet only: ${SUBNET}"
ufw allow from "$SUBNET" to any port 22 proto tcp comment 'lab: SSH from internal subnet'

echo "==> Enabling UFW"
ufw --force enable

echo
ufw status verbose
