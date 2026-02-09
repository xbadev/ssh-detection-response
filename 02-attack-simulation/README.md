# Phase 02: Attack Simulation

This phase demonstrates a **controlled SSH brute-force attack** from Kali Linux against Ubuntu Server to generate observable security events.  
The objective is to simulate realistic attack traffic, observe how failed authentication attempts appear in system logs, and establish a baseline for detection logic in later phases.

All attack activity is intentionally **non-destructive** and uses a minimal password list to ensure safe, controlled testing.

---

## Objective

Simulate a controlled SSH brute-force attempt from Kali Linux against Ubuntu Server and observe the resulting authentication logs.

This phase demonstrates:
- Internal network reachability (host-only network)
- How failed SSH authentication attempts appear in Ubuntu logs
- A safe, non-destructive attack simulation with a small password list

---

## Attack Scenario

**Attacker:**  
- Kali Linux (`192.168.56.30`)

**Target:**  
- Ubuntu Server SSH (`192.168.56.20:22`)

**Attack Tool:**  
- Hydra v9.6

**Wordlist:**  
- Custom 3-password list (`pw.txt`):
  - `password`
  - `123456`
  - `letmein`

**Monitoring:**  
- Real-time observation of `/var/log/auth.log` on Ubuntu using `sudo tail -f`

---

## Attack Execution

### Step 1: Connectivity Validation
Before launching the attack, network reachability was confirmed from Kali to Ubuntu:

```bash
ping -c 4 192.168.56.20
```

**Result:** 4 packets transmitted, 4 received, 0% packet loss

📸 **Evidence:** [Kali to Ubuntu Connectivity](evidence/screenshots/kali-to-ubuntu-connectivity.png)

---

### Step 2: Wordlist Preparation
A minimal wordlist was created with 3 weak passwords to simulate brute-force behavior without causing excessive log noise:

```bash
printf "password\n123456\nletmein\n" > pw.txt
```

This approach ensures the attack is **controlled and intentional**, demonstrating security observation without unnecessary system load.

---

### Step 3: Hydra Brute-Force Execution
Hydra was executed against the Ubuntu SSH service using the `bader` username:

```bash
hydra -l bader -P pw.txt ssh://192.168.56.20 -t 4 -V
```

**Parameters:**
- `-l bader` - Target username
- `-P pw.txt` - Password wordlist
- `-t 4` - 4 parallel tasks
- `-V` - Verbose output showing each attempt

**Result:** 0 valid passwords found (attack failed as expected)

📸 **Evidence:** [Hydra Attack Execution](evidence/screenshots/kali-hydra-attack.png)

---

### Step 4: Ubuntu Log Observation
During the attack, Ubuntu's authentication log was monitored in real-time:

```bash
sudo tail -f /var/log/auth.log
```

**Observed Events:**
- Authentication failures from `rhost=192.168.56.30`
- Failed password entries for user `bader`
- Connection closed messages during pre-authentication
- Clear correlation between Hydra attempts and log entries

📸 **Evidence:** [Ubuntu Authentication Log Failures](evidence/screenshots/ubuntu-authlog-failures.png)

---

## Attack Evidence Summary

📄 **[Full Attack Log](evidence/ssh-bruteforce-attack-log.txt)**

This log documents:
- Target and attacker details
- Connectivity validation results
- Wordlist contents
- Hydra command and output
- Ubuntu log observations

---

## Design Rationale

This attack simulation was intentionally designed to:

- **Generate observable security events** - Create failed authentication attempts in system logs
- **Use a minimal attack surface** - Only 3 password attempts to avoid log flooding
- **Maintain controlled execution** - Non-destructive testing with known outcomes
- **Establish detection baseline** - Provide clear attack signatures for monitoring scripts
- **Mirror real-world attack patterns** - SSH brute-force is a common reconnaissance technique

By executing this controlled attack, later phases can develop detection logic and automated response mechanisms based on real attack data.

---

## Validation

Attack execution and log observation were validated through:

✅ **Network reachability confirmed** - ICMP connectivity before attack  
✅ **Attack executed successfully** - Hydra completed all password attempts  
✅ **Logs captured authentication failures** - Ubuntu recorded all failed attempts from Kali IP  
✅ **No successful authentication** - Attack failed as designed  
✅ **Correlation verified** - Clear mapping between attack timing and log entries  

---

## Outcome

At the conclusion of this phase:

- SSH brute-force attack traffic was successfully generated
- Ubuntu authentication logs captured all failed login attempts
- Attack signatures are clearly observable and correlatable
- The environment is ready for detection logic development

This attack data enables Phase 03 (Detection & Observation) to build monitoring scripts that identify and alert on similar attack patterns.

---

## Documentation Structure

```
02-attack-simulation/
├── README.md                                      # This document
└── evidence/
    ├── ssh-bruteforce-attack-log.txt             # Complete attack execution log
    └── screenshots/
        ├── kali-to-ubuntu-connectivity.png       # Network reachability validation
        ├── kali-hydra-attack.png                 # Hydra execution and results
        └── ubuntu-authlog-failures.png           # Authentication log observations
```

---

## Next Phase

**→ [Phase 03: Detection & Observation](../03-detection-observation/)**

With attack signatures now generated and documented, the next phase develops detection logic to identify brute-force attempts in real-time and generate security alerts.
