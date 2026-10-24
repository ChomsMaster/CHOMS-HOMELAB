#!/bin/bash
cd /data/projects/choms-homelab/tools/choms-doctor

if [ -d /data/projects/choms-homelab/.venv ]; then
    /data/projects/choms-homelab/.venv/bin/python main.py
else
    python3 main.py
fi
