# Phase 0: Baseline Access Verification

## Objective
Establish a known-good baseline before performing any security attacks or defenses.

This phase confirms that SSH access is:
- Reachable
- Functional
- Observable

## Environment
- Host: Windows 11
- Attacker VM: Kali Linux (192.168.56.30)
- Target VM: Ubuntu Server (192.168.56.20)
- Network: VirtualBox Host-Only Adapter

## Actions Performed
- Verified SSH access from host to Ubuntu
- Verified SSH access from host to Kali
- Identified and corrected SSH service state on Kali

## Key Outcome
Both systems are accessible via SSH, providing a valid baseline for attack simulation.

All subsequent phases assume this baseline state.
