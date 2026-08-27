#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import socket
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONFIG = Path("/app/config.json")
STATE = Path("/state/state.json")
HEALTH = Path("/state/heartbeat")
HOST_STATUS = Path("/host-status/host-status.json")
TOKEN = Path("/run/secrets/telegram_bot_token")
CHAT_ID = Path("/run/secrets/telegram_chat_id")


def atomic_json(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True) + "\n")
    os.replace(tmp, path)


def telegram(status, name, detail):
    token = TOKEN.read_text().strip()
    chat_id = CHAT_ID.read_text().strip()
    message = f"{'🔥' if status == 'FIRING' else '✅'} {status} — RP3 external monitor — {name}: {detail}"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=body, method="POST"
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram HTTP {response.status}")


def endpoint(check, now):
    parsed = urllib.parse.urlparse(check["url"])
    started = time.monotonic()
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(parsed.hostname, 443)})
    context = ssl.create_default_context()
    with socket.create_connection((parsed.hostname, 443), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname=parsed.hostname) as tls:
            cert = tls.getpeercert()
    expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    tls_days = (expiry - now).total_seconds() / 86400
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443, timeout=15, context=context)
    connection.request(
        "GET",
        target,
        headers={
            "User-Agent": "choms-external-monitor/1",
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "close",
        },
    )
    response = connection.getresponse()
    status = response.status
    location = response.headers.get("Location", "")
    response.read(4096)
    connection.close()
    elapsed_ms = round((time.monotonic() - started) * 1000)
    errors = []
    if status != check["expected_status"]:
        errors.append(f"HTTP {status}, expected {check['expected_status']}")
    if check.get("location_contains") and check["location_contains"] not in location:
        errors.append("redirect target does not contain expected Authelia host")
    if tls_days < 0:
        errors.append("TLS certificate expired")
    return errors, f"dns={','.join(addresses)} http={status} tls_days={tls_days:.1f} response_ms={elapsed_ms}", tls_days, elapsed_ms


def local_status(config, now):
    data = json.loads(HOST_STATUS.read_text())
    errors = []
    age = now.timestamp() - data["timestamp"]
    limits = config["local_thresholds"]
    if age > config["host_status_max_age_seconds"]:
        errors.append(f"host helper stale ({age:.0f}s)")
    if data["disk_free_percent"] < limits["disk_free_percent_min"]:
        errors.append(f"microSD free {data['disk_free_percent']:.1f}%")
    if data["inode_free_percent"] < limits["inode_free_percent_min"]:
        errors.append(f"inode free {data['inode_free_percent']:.1f}%")
    if data["root_read_only"]:
        errors.append("root filesystem is read-only")
    if data.get("temperature_c") is not None and data["temperature_c"] > limits["temperature_c_max"]:
        errors.append(f"temperature {data['temperature_c']:.1f}C")
    if data.get("throttled") not in (None, "0x0", "0"):
        errors.append(f"throttling={data['throttled']}")
    if not data["firefox_running"]:
        errors.append("firefox-web is not running")
    detail = " ".join(f"{key}={value}" for key, value in data.items() if key != "timestamp")
    return errors, detail


def evaluate(name, errors, detail, states, failure_threshold):
    current = states.setdefault(name, {"failures": 0, "alerting": False})
    if errors:
        current["failures"] += 1
        if current["failures"] >= failure_threshold and not current["alerting"]:
            telegram("FIRING", name, "; ".join(errors))
            current["alerting"] = True
    else:
        current["failures"] = 0
        if current["alerting"]:
            telegram("RESOLVED", name, detail)
            current["alerting"] = False


def run_once(config, states):
    now = datetime.now(timezone.utc)
    for check in config["checks"]:
        try:
            errors, detail, tls_days, elapsed_ms = endpoint(check, now)
            if tls_days < config["tls_warning_days"]:
                errors.append(f"TLS expires in {tls_days:.1f} days")
            if elapsed_ms > config["response_warning_ms"]:
                errors.append(f"response time {elapsed_ms}ms")
        except Exception as error:
            errors, detail = [f"{type(error).__name__}: {error}"], "check failed"
        evaluate(check["name"], errors, detail, states, config["failure_threshold"])
    try:
        errors, detail = local_status(config, now)
    except Exception as error:
        errors, detail = [f"host status unavailable: {error}"], "host status check failed"
    evaluate("rp3-local", errors, detail, states, config["failure_threshold"])
    atomic_json(STATE, states)
    HEALTH.touch()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-notifications", action="store_true")
    args = parser.parse_args()
    if args.test_notifications:
        telegram("FIRING", "controlled-test", "synthetic notification; no service outage")
        telegram("RESOLVED", "controlled-test", "synthetic recovery")
        return
    config = json.loads(CONFIG.read_text())
    states = json.loads(STATE.read_text()) if STATE.exists() else {}
    while True:
        run_once(config, states)
        time.sleep(config["interval_seconds"])


if __name__ == "__main__":
    main()
