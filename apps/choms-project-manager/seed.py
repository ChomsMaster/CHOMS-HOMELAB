"""Read an optional private initial plan mounted at CAREER_SEED_FILE."""

import gzip
import json
import re
from datetime import date
from pathlib import Path

_MAX_BYTES = 4 * 1024 * 1024
_ID = re.compile(r"[A-Za-z0-9_-]{1,100}")
_HOUR = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")

def _unique_ids(records):
    ids = set()
    for record in records:
        identifier = record.get("id")
        if type(identifier) is not str or not _ID.fullmatch(identifier) or identifier in ids:
            raise ValueError("Invalid seed identifier")
        ids.add(identifier)


def load_seed(filename):
    """Load bounded, validated input without propagating private values in errors."""
    if not filename:
        return {}, [], {}
    try:
        path = Path(filename)
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as handle:
            raw = handle.read(_MAX_BYTES + 1)
        if len(raw) > _MAX_BYTES:
            raise ValueError("Seed exceeds input limit")
        data = json.loads(raw)
        project = data["project"]
        start = date.fromisoformat(project["start"]).isoformat()
        end = date.fromisoformat(project["end"]).isoformat()
        if start != project["start"] or end != project["end"] or end < start:
            raise ValueError("Invalid project bounds")
        tasks = data["tasks"]
        schedule = data["plan"]
        _unique_ids(tasks)
        if any(not isinstance(task.get("title"), str) or not task["title"].strip() for task in tasks):
            raise ValueError("Invalid task title")
        for transport in schedule:
            records = schedule[transport]
            _unique_ids(records)
            for record in records:
                day = record["date"]
                starts, ends = record["start"], record["end"]
                if (
                    day != date.fromisoformat(day).isoformat()
                    or not start <= day <= end
                    or not _HOUR.fullmatch(starts)
                    or (ends != "24:00" and not _HOUR.fullmatch(ends))
                    or starts >= ends
                    or not isinstance(record["title"], str)
                    or not isinstance(record["kind"], str)
                    or not isinstance(record["notes"], str)
                    or type(record["provisional"]) is not bool
                ):
                    raise ValueError("Invalid schedule occurrence")
    except (AttributeError, EOFError, KeyError, OSError, TypeError, ValueError, UnicodeError):
        raise RuntimeError("CAREER_SEED_FILE is invalid or unreadable") from None
    return project, tasks, schedule
