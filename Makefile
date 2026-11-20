# SSH Detection & Response — lab orchestration.
#
# Run on the Ubuntu target. Most targets need sudo; `make test` and
# `make status` do not. The repo can live anywhere (e.g. ~/ssh-detection-response);
# `make install` copies the runtime files to /opt/ssh-detection-response.
#
# Usage:
#   make help                  show this list
#   make test                  run the unit tests (no root, no services needed)
#   sudo make install          first-time install (service user, dirs, files, units)
#   sudo make config           edit /etc/ssh-detection-response/lab.env
#   sudo make enable           enable + start detector and responder
#   sudo make disable          stop + disable both services
#   make status                service status + last 5 alerts
#   sudo make reset            wipe alert history + state, unban attacker in Fail2Ban
#   sudo make demo             reset, then print the attacker-side command
#   sudo make uninstall        remove services + runtime files (keeps logs, config, ssh-dr user)

SHELL := /bin/bash
.DEFAULT_GOAL := help

# --- Constants ------------------------------------------------
INSTALL_DIR    := /opt/ssh-detection-response
CONFIG_DIR     := /etc/ssh-detection-response
STATE_DIR      := /var/lib/ssh-detection-response
LOG_DIR        := /var/log/ssh-detection-response
SERVICE_USER   := ssh-dr
DETECTOR_UNIT  := ssh-detector.service
RESPONDER_UNIT := ssh-responder.service

REPO_ROOT := $(CURDIR)

# --- Targets --------------------------------------------------

.PHONY: help
help:
	@sed -n '/^# Usage:/,/^[^#]/{/^# Usage:/d; /^[^#]/d; s/^# \{0,1\}//; p}' $(MAKEFILE_LIST)

.PHONY: test
test:
	python3 -m unittest discover -s tests -v

.PHONY: install
install: _root _deps _user _dirs _files _config _units
	@echo
	@echo "Install complete."
	@echo "  1. Edit config:        sudo make config   (webhook URL, MGMT_SUBNET, LAB_USER)"
	@echo "  2. Enable services:    sudo make enable"
	@echo "  3. Attack from Kali:   ./02-attack-simulation/run-attack.sh"

.PHONY: _root
_root:
	@if [[ $$EUID -ne 0 ]]; then echo "ERROR: this target needs sudo (try: sudo make $(MAKECMDGOALS))." >&2; exit 1; fi

.PHONY: _deps
_deps:
	@missing=""; for c in python3 rsync journalctl; do command -v $$c >/dev/null || missing="$$missing $$c"; done; \
	if [[ -n "$$missing" ]]; then echo "ERROR: missing:$$missing  (sudo apt-get install -y python3 rsync)" >&2; exit 1; fi

.PHONY: _user
_user:
	@if ! id -u $(SERVICE_USER) >/dev/null 2>&1; then \
		echo "==> creating system user $(SERVICE_USER)"; \
		useradd --system --no-create-home --shell /usr/sbin/nologin --user-group $(SERVICE_USER); \
	else \
		echo "==> system user $(SERVICE_USER) already exists"; \
	fi
	@usermod -a -G systemd-journal $(SERVICE_USER)

.PHONY: _dirs
_dirs:
	@echo "==> creating directories"
	install -d -m 0755 $(INSTALL_DIR)
	install -d -m 0755 $(CONFIG_DIR)
	install -d -m 0750 -o $(SERVICE_USER) -g $(SERVICE_USER) $(STATE_DIR)
	install -d -m 0755 -o $(SERVICE_USER) -g $(SERVICE_USER) $(LOG_DIR)

.PHONY: _files
_files:
	@echo "==> copying runtime files to $(INSTALL_DIR)"
	rsync -a --delete \
		--exclude='.git/' --exclude='.github/' --exclude='tests/' \
		--exclude='*.md' --exclude='**/evidence/' --exclude='**/screenshots/' \
		--exclude='lab.env' --exclude='Makefile' --exclude='.git*' \
		$(REPO_ROOT)/ $(INSTALL_DIR)/
	chmod 0755 $(INSTALL_DIR)/04-detection-monitoring/detector/ssh-bruteforce-detector.py
	chmod 0755 $(INSTALL_DIR)/05-automated-response/responder/ssh-responder.py
	chmod 0755 $(INSTALL_DIR)/02-attack-simulation/run-attack.sh
	chmod 0755 $(INSTALL_DIR)/03-defense-hardening/install-ufw.sh

.PHONY: _config
_config:
	@if [[ -f $(CONFIG_DIR)/lab.env ]]; then \
		echo "==> $(CONFIG_DIR)/lab.env exists, leaving it alone"; \
	else \
		echo "==> seeding $(CONFIG_DIR)/lab.env from lab.env.example"; \
		install -m 0640 -o root -g $(SERVICE_USER) $(REPO_ROOT)/lab.env.example $(CONFIG_DIR)/lab.env; \
	fi

.PHONY: _units
_units:
	@echo "==> installing systemd units"
	install -m 0644 $(REPO_ROOT)/04-detection-monitoring/systemd/$(DETECTOR_UNIT) /etc/systemd/system/$(DETECTOR_UNIT)
	install -m 0644 $(REPO_ROOT)/05-automated-response/systemd/$(RESPONDER_UNIT) /etc/systemd/system/$(RESPONDER_UNIT)
	systemctl daemon-reload

.PHONY: config
config: _root
	$${EDITOR:-nano} $(CONFIG_DIR)/lab.env
	@echo "==> restart to apply: sudo systemctl restart $(DETECTOR_UNIT) $(RESPONDER_UNIT)"

.PHONY: enable
enable: _root
	@if grep -q 'REPLACE_ME' $(CONFIG_DIR)/lab.env 2>/dev/null; then \
		echo "WARNING: ALERT_WEBHOOK_URL is still the placeholder; alerts will only be logged, not posted."; \
		echo "         Fix with: sudo make config"; \
	fi
	systemctl enable --now $(DETECTOR_UNIT) $(RESPONDER_UNIT)
	@$(MAKE) -s status

.PHONY: disable
disable: _root
	systemctl disable --now $(DETECTOR_UNIT) $(RESPONDER_UNIT) || true

.PHONY: status
status:
	@echo "==> $(DETECTOR_UNIT)"
	@systemctl --no-pager --lines=3 status $(DETECTOR_UNIT) || true
	@echo
	@echo "==> $(RESPONDER_UNIT)"
	@systemctl --no-pager --lines=3 status $(RESPONDER_UNIT) || true
	@echo
	@echo "==> recent alerts ($(LOG_DIR)/alerts.jsonl)"
	@if [[ -r $(LOG_DIR)/alerts.jsonl ]]; then tail -n 5 $(LOG_DIR)/alerts.jsonl; else echo "(none yet)"; fi

.PHONY: reset
reset: _root
	@echo "==> wiping state + alert history (services stay enabled)"
	systemctl stop $(DETECTOR_UNIT) $(RESPONDER_UNIT) 2>/dev/null || true
	rm -f $(STATE_DIR)/*.json $(LOG_DIR)/alerts.jsonl
	systemctl start $(DETECTOR_UNIT) $(RESPONDER_UNIT) 2>/dev/null || true
	@echo "==> clearing Fail2Ban bans (otherwise the attacker stays banned for bantime)"
	@fail2ban-client unban --all >/dev/null 2>&1 || echo "    (fail2ban not running; skipped)"
	@echo "==> ready for a clean demo run"

.PHONY: demo
demo: reset
	@echo
	@echo "================================================================"
	@echo " Demo ready. On Kali, run:"
	@echo "     ./02-attack-simulation/run-attack.sh"
	@echo
	@echo " Watch the pipeline here:"
	@echo "     sudo journalctl -u $(DETECTOR_UNIT) -u $(RESPONDER_UNIT) -f"
	@echo " Confirm the ban after the attack:"
	@echo "     sudo fail2ban-client status sshd"
	@echo "================================================================"

.PHONY: uninstall
uninstall: _root
	@echo "==> stopping and removing services"
	systemctl disable --now $(DETECTOR_UNIT) $(RESPONDER_UNIT) 2>/dev/null || true
	rm -f /etc/systemd/system/$(DETECTOR_UNIT) /etc/systemd/system/$(RESPONDER_UNIT)
	systemctl daemon-reload
	@echo "==> removing $(INSTALL_DIR) and $(STATE_DIR)"
	rm -rf $(INSTALL_DIR) $(STATE_DIR)
	@echo "==> kept $(LOG_DIR), $(CONFIG_DIR), and user $(SERVICE_USER) (remove manually if wanted)"
