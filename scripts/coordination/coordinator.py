"""Small private job ledger for Hermes -> Codex delegation.

This module contains no credential handling and never launches a shell. Job data
must be stored outside Git with owner-only permissions.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import uuid

MAX_TASK_CHARS = 12_000
JOB_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PROTECTED_WORKSPACES = {"chomsbios", "chomsboardview", "boardview"}
_WORKERS: dict[str, subprocess.Popen] = {}


class CoordinationError(ValueError):
    pass


def execution_env() -> dict[str, str]:
    # Do not forward provider/API/Git credentials from Hermes into child processes.
    keys = ("HOME", "PATH", "LANG", "LC_ALL", "TMPDIR", "XDG_CONFIG_HOME", "CODEX_HOME")
    env = {key: os.environ[key] for key in keys if os.environ.get(key)}
    return env


def private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise CoordinationError("state_directory_invalid")
    os.chmod(path, 0o700)
    return path.resolve()


def atomic_json(path: Path, value: dict) -> None:
    temp = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def load_job(state_dir: Path, job_id: str) -> tuple[Path, dict]:
    if not isinstance(job_id, str) or not JOB_RE.fullmatch(job_id):
        raise CoordinationError("invalid_job_id")
    root = private_dir(state_dir)
    folder = root / job_id
    if folder.is_symlink() or not folder.is_dir():
        raise CoordinationError("job_not_found")
    path = folder / "job.json"
    if path.is_symlink() or not path.is_file():
        raise CoordinationError("job_not_found")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("job_id") != job_id:
        raise CoordinationError("job_integrity_error")
    return folder, value


def submit(*, task: str, workspace: str, workspace_root: Path, state_dir: Path,
           codex: str = "codex", profile: str = "omniroute") -> dict:
    if not isinstance(task, str) or not task.strip() or len(task) > MAX_TASK_CHARS:
        raise CoordinationError("invalid_task")
    if profile != "omniroute":
        raise CoordinationError("invalid_codex_profile")
    root = workspace_root.resolve(strict=True)
    target = Path(workspace).resolve(strict=True)
    if not target.is_dir() or not target.is_relative_to(root):
        raise CoordinationError("workspace_outside_authorized_root")
    if any(re.sub(r"[^a-z0-9]", "", part.lower()) in PROTECTED_WORKSPACES for part in target.parts):
        raise CoordinationError("protected_workspace")
    git_root = target
    while git_root != root and not (git_root / ".git").exists():
        git_root = git_root.parent
    if not (git_root / ".git").exists():
        raise CoordinationError("workspace_must_be_git_repository")
    probe = subprocess.run(["git", "-C", str(target), "status", "--porcelain", "--untracked-files=all"],
                          capture_output=True, text=True, check=False)
    if probe.returncode != 0 or probe.stdout.strip():
        raise CoordinationError("workspace_must_be_clean_git_worktree")
    state = private_dir(state_dir)
    for existing in state.iterdir():
        if existing.is_symlink() or not existing.is_dir():
            continue
        job_file = existing / "job.json"
        try:
            current = json.loads(job_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if current.get("workspace") == str(target) and current.get("state") in ("queued", "running"):
            raise CoordinationError("workspace_has_active_job")
    job_id = str(uuid.uuid4())
    folder = state / job_id
    folder.mkdir(mode=0o700)
    now = time.time()
    record = {
        "schema": 1,
        "job_id": job_id,
        "state": "queued",
        "created_at": now,
        "updated_at": now,
        "workspace": str(target),
        "profile": profile,
        "task": task,
        "exit_code": None,
        "result_file": "result.txt",
        "diagnostic_file": "worker.log",
    }
    atomic_json(folder / "job.json", record)
    log_fd = os.open(folder / "worker.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(folder), "--codex", codex],
            stdin=subprocess.DEVNULL,
            stdout=log_fd,
            stderr=log_fd,
            close_fds=True,
            start_new_session=True,
            cwd=target,
            env=execution_env(),
        )
        _WORKERS[job_id] = child
    except Exception:
        record.update(state="failed", exit_code=127, updated_at=time.time(), error="worker_start_failed")
        atomic_json(folder / "job.json", record)
        raise CoordinationError("worker_start_failed") from None
    finally:
        os.close(log_fd)
    return {"job_id": job_id, "state": "queued", "workspace": str(target)}


def worker(folder: Path, *, codex: str) -> int:
    state_path = folder / "job.json"
    record = json.loads(state_path.read_text(encoding="utf-8"))
    folder = folder.resolve(strict=True)
    if record.get("state") != "queued" or record.get("schema") != 1:
        return 2
    record.update(state="running", updated_at=time.time())
    atomic_json(state_path, record)
    result = folder / "result.txt"
    # Codex supplies its ordinary configured approvals/sandbox. No bypass flags,
    # inherited task output, API keys, or existing session identifiers are used.
    argv = [codex, "exec", "--ephemeral", "--json", "--profile", record["profile"],
            "--cd", record["workspace"], "--output-last-message", str(result), record["task"]]
    try:
        completed = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, check=False)
        code = completed.returncode
        if result.exists():
            os.chmod(result, 0o600)
        record.update(state="succeeded" if code == 0 else "failed", exit_code=code,
                      updated_at=time.time())
    except OSError:
        record.update(state="failed", exit_code=127, updated_at=time.time(), error="codex_exec_failed")
    atomic_json(state_path, record)
    return int(record["exit_code"] or 0)


def status(*, job_id: str, state_dir: Path) -> dict:
    _, record = load_job(state_dir, job_id)
    child = _WORKERS.get(job_id)
    if child is not None:
        if record.get("state") in ("succeeded", "failed", "cancelled"):
            try:
                child.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                pass
        if child.poll() is not None:
            _WORKERS.pop(job_id, None)
    return {k: record.get(k) for k in ("job_id", "state", "created_at", "updated_at", "exit_code", "workspace")}


def result(*, job_id: str, state_dir: Path, max_chars: int = 20_000) -> dict:
    folder, record = load_job(state_dir, job_id)
    if record.get("state") not in ("succeeded", "failed"):
        raise CoordinationError("job_not_terminal")
    path = folder / record["result_file"]
    if path.is_symlink() or not path.is_file():
        return {"job_id": job_id, "state": record["state"], "exit_code": record["exit_code"], "result": ""}
    content = path.read_text(encoding="utf-8", errors="replace")
    return {"job_id": job_id, "state": record["state"], "exit_code": record["exit_code"],
            "result": content[:max_chars], "truncated": len(content) > max_chars}


def remove(*, job_id: str, state_dir: Path, explicit: bool) -> dict:
    if explicit is not True:
        raise CoordinationError("explicit_cleanup_required")
    folder, record = load_job(state_dir, job_id)
    if record.get("state") not in ("succeeded", "failed", "cancelled"):
        raise CoordinationError("job_not_terminal")
    # Deliberately remove only known files in this exact UUID directory.
    for name in ("job.json", "result.txt", "worker.log"):
        p = folder / name
        if p.is_symlink():
            raise CoordinationError("job_integrity_error")
        if p.exists():
            p.unlink()
    folder.rmdir()
    return {"job_id": job_id, "state": "removed"}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    if args.worker:
        raise SystemExit(worker(args.worker, codex=args.codex))
    raise SystemExit("MCP transport is provided by choms_coordinator_mcp.py")


if __name__ == "__main__":
    main()
