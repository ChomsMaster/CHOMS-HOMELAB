# Power Recovery Validation

## Objective

Validate that CHOMS-HOMELAB can recover automatically after a complete power loss.

## BIOS Configuration

The Mini PC BIOS does not expose a "Last State" option.

Configured option:

- State After G3: Power On

## Validation Result

Status: PASSED

## Test Procedure

1. Server was powered off by removing power.
2. Power was restored.
3. Mini PC powered on automatically.
4. Debian 13 booted successfully.
5. Network connectivity was restored.
6. SSH became available.
7. Docker started automatically.
8. WireGuard started automatically.
9. Pi-hole started automatically.
10. Nginx started automatically.
11. PostgreSQL started automatically.

## Validated Services

| Component | Status |
|---|---|
| Debian 13 | Passed |
| Docker | Passed |
| WireGuard | Passed |
| Pi-hole | Passed |
| Nginx | Passed |
| PostgreSQL | Passed |
| SSH | Passed |
| /data mount | Passed |

## Notes

Wake-on-LAN was investigated but the BIOS does not expose a clear Wake-on-LAN, PME, PCIe Wake or Resume by LAN option.

The network card reports Wake-on-LAN support from Linux, but final Wake-on-LAN validation remains pending.

Current production power recovery strategy is based on BIOS automatic power-on after AC restoration.
