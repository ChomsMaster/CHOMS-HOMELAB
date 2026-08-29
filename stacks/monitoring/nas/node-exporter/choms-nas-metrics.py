#!/usr/bin/env python3

import datetime
import json
import os
import pathlib
import re
import subprocess
import tempfile
import urllib.request


OUTPUT_DIR = pathlib.Path("/home/chomsmaster/choms-node-exporter/textfile")
OUTPUT = OUTPUT_DIR / "choms_nas.prom"
SCRUTINY_SUMMARY = "https://scrutiny.chomsmaster.com/api/summary"
SCRUTINY_STALE_SECONDS = 8 * 60 * 60


def service_active(name):
    return int(
        subprocess.run(
            ["/usr/bin/systemctl", "is-active", "--quiet", name],
            check=False,
        ).returncode
        == 0
    )


def raid_state():
    text = pathlib.Path("/proc/mdstat").read_text(encoding="utf-8")
    match = re.search(
        r"^md0\s*:\s*active\s+raid5\b.*?\n.*?\[(\d+)/(\d+)\]\s+\[([U_]+)\]",
        text,
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError("expected md0 RAID5 status is absent")
    expected, active, bitmap = int(match.group(1)), int(match.group(2)), match.group(3)
    healthy = int(expected == 4 and active == 4 and bitmap == "UUUU")
    return expected, active, healthy


def storage_export_present():
    lines = pathlib.Path("/var/lib/nfs/etab").read_text(encoding="utf-8").splitlines()
    return int(any(line.split(maxsplit=1)[0] == "/srv/storage" for line in lines if line))


def scrutiny_state():
    with urllib.request.urlopen(SCRUTINY_SUMMARY, timeout=10) as response:
        summary = json.load(response)["data"]["summary"]
    records = [
        record
        for record in summary.values()
        if record.get("device", {}).get("host_id") == "choms-nas"
    ]
    if len(records) != 5:
        raise RuntimeError("expected exactly five NAS devices in Scrutiny")
    timestamps = []
    for record in records:
        raw = record.get("smart", {}).get("collector_date", "")
        timestamps.append(datetime.datetime.fromisoformat(raw.replace("Z", "+00:00")))
    latest = max(timestamps)
    age = (datetime.datetime.now(datetime.timezone.utc) - latest).total_seconds()
    return latest.timestamp(), int(age > SCRUTINY_STALE_SECONDS), len(records)


def metric(name, help_text, value):
    return [f"# HELP {name} {help_text}", f"# TYPE {name} gauge", f"{name} {value}"]


def main():
    expected, active, raid_healthy = raid_state()
    last_success, stale, devices = scrutiny_state()
    lines = []
    lines += metric("choms_nas_nfs_service_active", "Whether the NAS NFS service is active.", service_active("nfs-server.service"))
    lines += metric("choms_nas_nfs_storage_export_present", "Whether /srv/storage is present in the effective NFS export table.", storage_export_present())
    lines += metric("choms_nas_mdmonitor_active", "Whether mdmonitor.service is active.", service_active("mdmonitor.service"))
    lines += metric("choms_nas_raid_healthy", "Whether md0 is RAID5 with all four members active.", raid_healthy)
    lines += metric("choms_nas_raid_members_expected", "Expected md0 member count.", expected)
    lines += metric("choms_nas_raid_members_active", "Active md0 member count.", active)
    lines += metric("choms_nas_scrutiny_last_success_unixtime", "Unix time of the latest NAS Scrutiny publication.", f"{last_success:.0f}")
    lines += metric("choms_nas_scrutiny_collector_stale", "Whether the latest NAS Scrutiny publication is older than eight hours.", stale)
    lines += metric("choms_nas_scrutiny_devices", "NAS devices represented by fresh Scrutiny collector identity.", devices)
    lines += metric("choms_nas_textfile_collection_success", "Whether the last atomic NAS metric collection completed.", 1)
    payload = "\n".join(lines) + "\n"

    OUTPUT_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".choms_nas.", dir=OUTPUT_DIR, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, OUTPUT)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == "__main__":
    main()
