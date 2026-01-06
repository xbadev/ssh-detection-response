# Firewall Considerations

This lab focuses primarily on network segmentation and controlled access rather than full firewall hardening.

## Current State
- No custom firewall rules applied initially
- Network isolation achieved through VirtualBox Host-Only and NAT adapters
- SSH used as the primary remote access method

## Rationale
Firewall configuration was intentionally deferred to:
- First validate correct network topology and routing
- Avoid masking networking issues with firewall rules
- Establish baseline connectivity before applying restrictions

## Planned Enhancements
Future iterations of this lab may include:
- Enabling UFW on Ubuntu Server
- Restricting SSH access to the host-only subnet
- Denying all other inbound traffic by default
- Logging blocked connection attempts

This approach mirrors real-world workflows where connectivity is validated before security hardening is applied.
