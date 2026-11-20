#!/usr/bin/env bash
# ============================================================
# Phase 03 — UFW install
# ============================================================
# Default-deny inbound, then allow SSH from:
#   - INTERNAL_SUBNET (vmbr1 lab subnet — where the attacker lives)
#   - MGMT_SUBNET     (where you administer the VM from, e.g. home LAN)
#
# Lockout guard: before touching the firewall, the script looks at every
# established SSH session on this host. If any of them comes from an IP
# outside both allowed subnets, it stops — enabling UFW would drop that
# session. Pass --force to override (e.g. when you're on the Proxmox
# console and don't care about SSH sessions).
#
# Usage:  sudo ./install-ufw.sh [--force]
# ============================================================

set -euo pipefail

LAB_ENV="${LAB_ENV:-/etc/ssh-detection-response/lab.env}"
FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: must run as root (use sudo)." >&2
    exit 1
fi

if [[ ! -r "$LAB_ENV" ]]; then
    echo "ERROR: cannot read $LAB_ENV (run 'sudo make install' first)." >&2
    exit 2
fi

# shellcheck disable=SC1090
source "$LAB_ENV"
INTERNAL="${INTERNAL_SUBNET:?INTERNAL_SUBNET not set in $LAB_ENV}"
MGMT="${MGMT_SUBNET:-}"

# True if IP $1 is inside CIDR $2.
in_subnet() {
    python3 -c 'import ipaddress, sys
ip = ipaddress.ip_address(sys.argv[1])
if getattr(ip, "ipv4_mapped", None):
    ip = ip.ipv4_mapped
sys.exit(0 if ip in ipaddress.ip_network(sys.argv[2], strict=False) else 1)' "$1" "$2" 2>/dev/null
}

# --- Lockout guard ------------------------------------------------
echo "==> Checking current SSH sessions against allowed subnets"
stranded=()
while read -r peer; do
    [[ -z "$peer" ]] && continue
    ip="${peer%:*}"          # drop :port
    ip="${ip#[}"; ip="${ip%]}"
    ok=0
    in_subnet "$ip" "$INTERNAL" && ok=1
    [[ -n "$MGMT" ]] && in_subnet "$ip" "$MGMT" && ok=1
    [[ $ok -eq 0 ]] && stranded+=("$ip")
done < <(ss -Htn state established '( sport = :22 )' | awk '{print $4}')

if [[ ${#stranded[@]} -gt 0 && $FORCE -eq 0 ]]; then
    echo "ERROR: these active SSH sessions would be cut off by the new rules:" >&2
    printf '         %s\n' "${stranded[@]}" >&2
    echo "       Set MGMT_SUBNET in $LAB_ENV to cover them, or re-run with --force." >&2
    exit 3
fi

# --- Apply rules --------------------------------------------------
echo "==> Resetting UFW to a known state"
ufw --force reset >/dev/null

echo "==> Default policies: deny incoming, allow outgoing"
ufw default deny incoming
ufw default allow outgoing

echo "==> Allowing SSH from internal lab subnet: ${INTERNAL}"
ufw allow from "$INTERNAL" to any port 22 proto tcp comment 'lab: SSH from internal subnet'

if [[ -n "$MGMT" ]]; then
    echo "==> Allowing SSH from management subnet: ${MGMT}"
    ufw allow from "$MGMT" to any port 22 proto tcp comment 'lab: SSH from management subnet'
fi

echo "==> Enabling UFW"
ufw --force enable

echo
ufw status verbose
