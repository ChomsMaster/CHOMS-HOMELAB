# CHOMS Node Lifecycle

Node creation

↓

Bootstrap

↓

Install Docker

↓

Install CHOMS Node Agent

↓

Enable systemd timer

↓

Create node.yaml

↓

Ready

Every two minutes:

↓

Agent wakes up

↓

Reads:

- hostname
- role
- local IP

↓

If changes detected:

- update state
- log changes

↓

Sleep again
