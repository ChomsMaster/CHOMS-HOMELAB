"""Verify source hashes from the local audit and write a path-free dedup index.

Original skills are read in place and never copied, linked, rewritten, or activated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def source_class(path: Path, home: Path, repo: Path) -> str | None:
    roots = (
        (home / ".hermes/skills", "hermes"),
        (home / ".codex/skills", "codex"),
        (home / ".agents/skills", "agents"),
        (home / ".local/share/choms-skills/runtime-v1", "choms-runtime"),
        (repo / "tools/choms-skills", "choms-platforms"),
    )
    resolved = path.resolve(strict=True)
    for root, label in roots:
        try:
            resolved.relative_to(root.resolve(strict=True))
            return label
        except (ValueError, FileNotFoundError):
            continue
    return None


def inventory(audit: Path, repo: Path) -> dict:
    audit = audit.resolve(strict=True)
    home = Path.home().resolve(strict=True)
    data = json.loads((audit / "CHOMS_SKILLS_FUNCTIONAL_ANALYSIS.json").read_text(encoding="utf-8"))
    skills = data.get("skills")
    if not isinstance(skills, dict) or len(skills) != data.get("total_skills"):
        raise ValueError("audit_schema_mismatch")
    source_records = []
    for host in ("node-dev-01", "node-dev-02"):
        filename = f"{host}-skills.json"
        host_data = json.loads((audit / filename).read_text(encoding="utf-8"))
        if host_data.get("host") != host or not isinstance(host_data.get("skills"), list):
            raise ValueError("host_audit_schema_mismatch")
        source_records.extend({**record, "host": host} for record in host_data["skills"])
    comparison = json.loads((audit / "choms-unified-skills-comparison.json").read_text(encoding="utf-8"))
    if len(source_records) != comparison.get("total_records") or len(skills) != comparison.get("unique_names"):
        raise ValueError("host_source_count_mismatch")
    entries = []
    content_groups: dict[str, list[dict[str, str]]] = {}
    source_failures = 0
    by_name: dict[str, list[dict]] = {}
    for record in source_records:
        name = record.get("name")
        if not isinstance(name, str) or name not in skills:
            raise ValueError("host_skill_not_in_functional_audit")
        by_name.setdefault(name, []).append(record)
    if set(by_name) != set(skills):
        raise ValueError("host_skill_set_mismatch")
    for name, records in sorted(by_name.items()):
        # Preserve both host snapshots as read-only metadata; never merge/delete files.
        verified = []
        for record in records:
            path = Path(record["path"])
            try:
                kind = source_class(path, home, repo)
                if kind is None or not path.is_file() or path.is_symlink():
                    raise ValueError("source_outside_review_roots")
                content = path.read_bytes()
                digest = hashlib.sha256(content).hexdigest()
                if digest != record.get("sha256") or len(content) != record.get("bytes"):
                    raise ValueError("source_changed_since_audit")
                verified.append({"sha256": digest, "bytes": len(content), "source_class": kind})
                content_groups.setdefault(digest, []).append({"name": name, "host": record["host"]})
            except (OSError, ValueError, KeyError, TypeError):
                source_failures += 1
                verified.append({"sha256": record.get("sha256"), "bytes": record.get("bytes"),
                                 "source_class": "unverified"})
        actual_hashes = {x["sha256"] for x in verified if x["source_class"] != "unverified"}
        digest = next(iter(actual_hashes)) if len(actual_hashes) == 1 and len(verified) == len(records) else None
        entries.append({"name": name, "sha256": digest, "bytes": verified[0]["bytes"] if digest else None,
                        "sources": verified, "functional_review": "pending",
                        "security_review": "pending", "activation": "blocked"})
    groups = []
    for digest, names in sorted(content_groups.items()):
        unique = sorted({(x["name"],x["host"]) for x in names})
        if len(unique) > 1:
            groups.append({"sha256": digest, "sources": [{"name":n,"host":h} for n,h in unique]})
    return {
        "schema_version": 1,
        "source_audit": "~/choms-skill-audit/{node-dev-01-skills.json,node-dev-02-skills.json,choms-unified-skills-comparison.json,CHOMS_SKILLS_FUNCTIONAL_ANALYSIS.json}",
        "source_preservation": "read-only; source files are not copied, linked, rewritten, or activated",
        "deduplication": "group-by-sha256; originals remain at their source locations",
        "counts": {"skills": len(entries), "source_records": len(source_records), "verified_source_records": sum(
            s["source_class"] != "unverified" for e in entries for s in e["sources"]),
            "unverified_source_records": source_failures,
            "exact_duplicate_groups": len(groups)},
        "exact_duplicate_groups": groups,
        "skills": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=Path.home() / "choms-skill-audit")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.audit_dir, args.repo_root.resolve(strict=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"counts": result["counts"], "output": str(args.output), "status":
                      "PASS" if result["counts"]["unverified_source_records"] == 0 else "PARTIAL"}))


if __name__ == "__main__":
    main()
