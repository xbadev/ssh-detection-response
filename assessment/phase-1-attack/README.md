# Phase 1: Attack Simulation (Kali -> Ubuntu SSH)

## Objective
Simulate a controlled SSH brute-force attempt from Kali Linux against Ubuntu Server and observe the resulting authentication logs.

This phase demonstrates:
- Internal network reachability (host-only network)
- How failed SSH authentication attempts appear in Ubuntu logs
- A safe, non-destructive attack simulation with a small password list

## Setup
- Attacker: Kali Linux (192.168.56.30)
- Target: Ubuntu Server (192.168.56.20)
- Service: SSH on port 22
- Monitoring: `sudo tail -f /var/log/auth.log` on Ubuntu

## Steps Performed
1) Confirmed reachability from Kali to Ubuntu using ICMP ping.
2) Created a small wordlist (`pw.txt`) with 3 passwords.
3) Ran Hydra against Ubuntu SSH using the username `bader`.
4) Observed and captured Ubuntu `auth.log` entries during the attempts.

## Results
- Hydra attempted 3 passwords and found 0 valid credentials.
- Ubuntu logged authentication failures and failed password entries from 192.168.56.30.

## Evidence
- Kali connectivity and wordlist creation: `screenshots/kali-connectivity-and-wordlist.png`
- Hydra attempt output: `screenshots/kali-hydra-ssh-bruteforce.png`
- Ubuntu auth.log failures from Kali IP: `screenshots/ubuntu-authlog-failures.png`
- Trimmed evidence summary: `attack-log.txt`
