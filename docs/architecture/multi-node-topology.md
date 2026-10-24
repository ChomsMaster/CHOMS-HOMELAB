# CHOMS Multi-node Topology

## Current topology

```text
Internet
   |
DIGI Router (192.168.1.1)
   |
D-Link DGS-1016D Gigabit Switch
   |-- choms-node-01 192.168.1.138
   |-- choms-node-02 192.168.1.172
   |-- choms-nas     192.168.1.167
   |-- TV / clients
```

## Design decision

Nodes should execute services. The NAS should store shared data.

Current exceptions are allowed during transition, such as node-01 still having a local SSD media library at `/media/ssd-media`.

## Naming convention

```text
choms-nas
choms-node-01
choms-node-02
choms-node-03
choms-router
choms-switch-01
```

Avoid hardware-dependent names. If hardware changes, the role name should remain valid.

## Traffic behavior

Internal traffic between nodes and NAS does not traverse the router. It is switched directly by the D-Link. The router is only involved for traffic to/from WAN, gateway/DHCP functions, or inter-subnet routing if introduced later.
