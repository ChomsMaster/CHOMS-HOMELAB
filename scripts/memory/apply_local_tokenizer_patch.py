#!/usr/bin/env python3
"""Apply the reviewed patch with exact hashes, positions and context (fuzz=0)."""
import hashlib
import json
from pathlib import Path
import re
import sys


def apply_exact(original, chunks):
    lines = original.splitlines(keepends=True)
    result = []
    cursor = 0
    index = 0
    while index < len(chunks):
        match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n?", chunks[index])
        if not match:
            raise ValueError("Invalid patch hunk")
        start, count, new_start, new_count = (int(match[1]), int(match[2] or 1),
                                              int(match[3]), int(match[4] or 1))
        if start - 1 < cursor or start - 1 > len(lines):
            raise ValueError("Patch offset forbidden")
        result.extend(lines[cursor:start - 1])
        cursor = start - 1
        if len(result) != new_start - 1:
            raise ValueError("Patch output offset forbidden")
        used = added = 0
        index += 1
        while index < len(chunks) and not chunks[index].startswith("@@ "):
            line = chunks[index]
            if line[:1] not in (" ", "+", "-"):
                raise ValueError("Invalid patch line")
            if line[:1] in (" ", "-"):
                if cursor >= len(lines) or lines[cursor] != line[1:]:
                    raise ValueError("Patch context mismatch: fuzz forbidden")
                cursor += 1
                used += 1
            if line[:1] in (" ", "+"):
                result.append(line[1:])
                added += 1
            index += 1
        if used != count or added != new_count:
            raise ValueError("Patch hunk count mismatch")
    result.extend(lines[cursor:])
    return "".join(result)


def inventory(root):
    return {str(p.relative_to(root)): (p.lstat().st_size, p.lstat().st_mtime_ns,
                                     p.lstat().st_mode, p.lstat().st_uid, p.lstat().st_gid)
            for p in root.rglob("*") if not p.is_dir()}


def main():
    root, inputs = Path(sys.argv[1]), Path(sys.argv[2])
    metadata = json.loads((inputs / "local-tokenizer-patch.json").read_text())
    patch = inputs / "cognee-1.6.5-local-tokenizer.patch"
    if hashlib.sha256(patch.read_bytes()).hexdigest() != metadata["patch_sha256"]:
        raise ValueError("Patch checksum mismatch")
    expected = {f["path"]: f for f in metadata["files"]}
    if len(expected) != 4:
        raise ValueError("Exactly four original files required")
    before = inventory(root)
    prepared = {}
    lines = patch.read_text().splitlines(keepends=True)
    index = 0
    while index < len(lines):
        if not lines[index].startswith("--- a/") or index + 1 >= len(lines):
            raise ValueError("Invalid patch header")
        name = lines[index][6:].rstrip("\n")
        if lines[index + 1] != "+++ b/" + name + "\n" or name not in expected or name in prepared:
            raise ValueError("Unexpected patch target")
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe patch path")
        path = root / rel
        if path.is_symlink() or not path.is_file():
            raise ValueError("Invalid original file")
        original = path.read_bytes()
        if hashlib.sha256(original).hexdigest() != expected[name]["base_sha256"]:
            raise ValueError("Original source checksum mismatch")
        index += 2
        end = index
        while end < len(lines) and not lines[end].startswith("--- a/"):
            end += 1
        updated = apply_exact(original.decode(), lines[index:end]).encode()
        if hashlib.sha256(updated).hexdigest() != expected[name]["patched_sha256"]:
            raise ValueError("Patched source checksum mismatch")
        compile(updated, name, "exec")
        prepared[name] = updated
        index = end
    if set(prepared) != set(expected):
        raise ValueError("Incomplete patch")
    for name, data in prepared.items():
        (root / name).write_bytes(data)
    after = inventory(root)
    changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    if changed != set(expected):
        raise ValueError("Additional or missing filesystem changes")
    print("PATCH_EXACT_FUZZ0=PASS FILES=4")


if __name__ == "__main__":
    main()
