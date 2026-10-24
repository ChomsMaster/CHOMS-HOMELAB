#!/usr/bin/env python3
import time
from pathlib import Path

heartbeat = Path("/state/heartbeat")
if not heartbeat.exists() or time.time() - heartbeat.stat().st_mtime > 180:
    raise SystemExit(1)
