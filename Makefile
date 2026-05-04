# SSH Detection & Response — lab orchestration.
#
# Run on the Ubuntu target (most targets need root).
# All paths are intentional — repo lives in /home/<you>, install
# copies the runtime files to /opt/ssh-detection-response.
#
# Usage:
#   make help                  show this list
#   sudo make install          first-time install (system user, dirs, files, units)
#   sudo make config           open /etc/ssh-detection-response/lab.env in editor
#   sudo make enable           enable + start detector and responder
#   sudo make disable          stop + disable services (lab off)
#   make status                show detector and responder status + recent alerts
#   sudo make uninstall        remove services, files, system user (keeps logs)
#   sudo make demo             reset state, attack-ready prompt
#   sudo make reset            wipe runtime state and alert history (no install changes)

SHELL := /bin/bash
.DEFAULT_GOAL := help

# --- Constants ------------------------------------------------
INSTALL_DIR := /opt/ssh-detection-response
CONFIG_DIR  := /etc/ssh-detection-response
STATE_DIR   := /var/lib/ssh-detection-response
LOG_DIR     := /var/log/ssh-detection-response
SERVICE_USER := ssh-dr
DETECTOR_UNIT := ssh-detector.service
RESPONDER_UNIT := ssh-responder.service

REPO_ROOT := $(shell pwd)

# --- Helpers --------------------------------------------------
define require_root
	@if [[ $$EUID -ne 0 ]]; then echo "ERROR: '$@' requires sudo." >&2; exit 1; fi
endef

# --- Targets --------------------------------------------------

.PHONY: help
help:
	@sed -n '/^# Usage:/,/^[^#]/{/^# Usage:/d; /^[^#]/d; s/^# \{0,1\}//; p}' $(MAKEFILE_LIST)

.PHONY: install
install: _root _user _dirs _files _config _units
	@echo
	@echo "Install complete."
	@echo "  1. Edit config:        sudo make config"
	@echo "  2. Enable services:    sudo make enable"
	@echo "  3. Run from Kali:      ./02-attack-simulation/run-attack.sh"

.PHONY: _root
_root:
	$(call require_root)

.PHONY: _user
_user:
	@if ! id -u $(SERVICE_USER) >/dev/null 2>&1; then \
		echo "==> creating system user $(SERVICE_USER)"; \
		useradd --system --no-create-home --shell /usr/sbin/nologin --user-group $(SERVICE_USER); \
		usermod -a -G systemd-journal $(SERVICE_USER); \
	else \
		echo "==> system user $(SERVICE_USER) already exists"; \
	fi

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
		--exclude='.git/' --exclude='*.md' --exclude='**/evidence/' \
		--exclude='**/screenshots/' --exclude='**/network/evidence/' \
		--exclude='**/configs/evidence/' --exclude='lab.env' \
		--exclude='Makefile' --exclude='.gitignore' \
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
	$${EDITOR:-vi} $(CONFIG_DIR)/lab.env

.PHONY: enable
enable: _root
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
	@echo "==> wiping state + alert history (services kept enabled)"
	systemctl stop $(DETECTOR_UNIT) $(RESPONDER_UNIT) 2>/dev/null || true
	rm -f $(STATE_DIR)/*.json $(LOG_DIR)/alerts.jsonl
	systemctl start $(DETECTOR_UNIT) $(RESPONDER_UNIT) 2>/dev/null || true
	@echo "==> ready for a clean demo run"

.PHONY: demo
demo: _root reset
	@echo
	@echo "================================================================"
	@echo " Demo ready. From Kali, run:"
	@echo "     ./02-attack-simulation/run-attack.sh"
	@echo
	@echo " Watch alerts in real time:"
	@echo "     sudo journalctl -u $(DETECTOR_UNIT) -u $(RESPONDER_UNIT) -f"
	@echo "================================================================"

.PHONY: uninstall
uninstall: _root
	@echo "==> stopping and removing services"
	systemctl disable --now $(DETECTOR_UNIT) $(RESPONDER_UNIT) 2>/dev/null || true
	rm -f /etc/systemd/system/$(DETECTOR_UNIT) /etc/systemd/system/$(RESPONDER_UNIT)
	systemctl daemon-reload
	@echo "==> removing $(INSTALL_DIR) and $(STATE_DIR)"
	rm -rf $(INSTALL_DIR) $(STATE_DIR)
	@echo "==> keeping $(LOG_DIR) and $(CONFIG_DIR) (delete manually if you want them gone)"
	@echo "==> keeping system user $(SERVICE_USER) (use 'userdel $(SERVICE_USER)' to remove)"
