# LAN Validation — 2026-07-03

## Objective

Validate whether the DIGI router, D-Link switch, cables, or server NICs were responsible for Jellyfin/TV playback interruptions.

## Findings

### Link negotiation

Node-01 Ethernet link:

```text
Speed: 1000Mb/s
Duplex: Full
Auto-negotiation: on
Link detected: yes
```

### Ping validation

Ping tests between nodes/NAS and the router showed low latency and 0% packet loss.

### iperf3 validation

| Source | Destination | Approx throughput | Retransmissions |
|---|---:|---:|---:|
| node-01 | node-02 | 941 Mbps | 0 |
| node-02 | node-01 | 830 Mbps | 0 |
| node-01 | NAS | 884-885 Mbps | 0 |
| NAS | node-01 | 753 Mbps | 0 |
| NAS | node-02 | 813-814 Mbps | 0 |
| node-02 | NAS | 829-830 Mbps | 0 |

## Conclusion

The LAN backbone is considered healthy.

- Router: not suspected.
- D-Link DGS-1016D switch: not suspected globally.
- Main cabling/server NICs: validated.
- Differences by direction are normal for heterogeneous hosts.

The likely TV/Jellyfin problem is localized to the TV/client path: TV app, DLNA behavior, TV Ethernet port, or the RJ45 cable/connector with broken locking tab.

## Operational note

`iperf3` uses TCP port `5201`. UFW blocks it unless opened:

```bash
sudo ufw allow 5201/tcp
```

After diagnostics, close it again:

```bash
sudo ufw delete allow 5201/tcp
sudo ufw reload
```
