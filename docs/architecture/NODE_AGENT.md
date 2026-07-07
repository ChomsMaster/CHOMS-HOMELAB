# CHOMS Node Agent

## Purpose

The CHOMS Node Agent is a lightweight local agent installed on every CHOMS node.

It is executed by a systemd timer and does not run permanently.

## Responsibilities

- Detect local node identity
- Detect local IP
- Detect hostname
- Detect role
- Store last known state
- Log changes
- Prepare future heartbeat integration with CHOMS Controller

## Runtime paths

Config:

    /opt/choms/node.yaml

State:

    /var/lib/choms/agent/node-state.env

Logs:

    /var/log/choms/choms-node-agent.log

## Timers

All nodes:

    choms-node-agent.timer

Edge node only:

    choms-ddns-namecheap.timer

## Rule

Public DDNS runs only on the Edge node.
