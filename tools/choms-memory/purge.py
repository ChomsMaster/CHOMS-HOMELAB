"""Versioned, registry-only logical purge for Cognee 1.6.5 / Ladybug 0.19.0.

The caller fences all writers and commits purge_pending before calling this module.
No user-provided path or dataset name is accepted by the public adapter.
"""
import os
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path

CONTRACT = "cognee-1.6.5-ladybug-0.19.0-v1"
SUFFIXES = ("", ".wal", ".lock", ".shadow", ".tmp", ".wal.checkpoint",
            ".checkpoint.intent.lock", ".checkpoint.apply.lock")


class PurgePending(RuntimeError):
    """Sanitized failure: caller must retain its content-free reconciliation record."""


@dataclass(frozen=True)
class RegistryEntry:
    owner_id: str
    dataset_id: str
    exclusive: bool
    contract: str = CONTRACT

    def names(self):
        if not self.exclusive or self.contract != CONTRACT:
            raise PurgePending("dataset_not_exclusive_or_version_mismatch")
        for value in (self.owner_id, self.dataset_id):
            try:
                if str(uuid.UUID(value)) != value:
                    raise ValueError
            except (ValueError, TypeError, AttributeError):
                raise PurgePending("invalid_registry_id") from None
        return tuple(self.dataset_id + ".pkl" + suffix for suffix in SUFFIXES)


def open_trusted_root(root):
    """Walk without resolving links. Return an fd anchored to the trusted directory."""
    path = Path(root)
    if not path.is_absolute() or ".." in path.parts:
        raise PurgePending("invalid_root")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            new = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                          dir_fd=fd)
            os.close(fd)
            fd = new
        s = os.fstat(fd)
        if s.st_uid != os.geteuid() or stat.S_IMODE(s.st_mode) != 0o700:
            raise PurgePending("untrusted_root_permissions")
        return fd
    except BaseException:
        os.close(fd)
        raise


def inventory(fd, names):
    """Closed directory, not a prefix scan: any unregistered object blocks deletion."""
    observed = os.listdir(fd)
    if set(observed) - set(names):
        raise PurgePending("unexpected_artifact")
    result = {}
    for name in observed:
        s = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
            raise PurgePending("unexpected_type_or_link")
        result[name] = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    return result


async def purge(root, entry, official_delete, *, checkpoint=None):
    """Official deletion first, then exact leftovers. Never report a partial success.

    The root is service configuration; entry is read from the private registry under
    a DB transaction/advisory lock. Root and owner directories are private to this
    service. No other process may write during the call. No subgraphs are allowed.
    checkpoint is only an interruption injection point for offline regression tests.
    """
    names = entry.names()
    root_fd = child_fd = None
    try:
        root_fd = open_trusted_root(root)
        try:
            child_fd = os.open(entry.owner_id,
                               os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=root_fd)
        except FileNotFoundError:
            # Keep a private empty owner directory even for absent datasets so
            # the official callback cannot bypass the final inventory check.
            os.mkdir(entry.owner_id, mode=0o700, dir_fd=root_fd)
            child_fd = os.open(entry.owner_id,
                               os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=root_fd)
        s = os.fstat(child_fd)
        if s.st_uid != os.geteuid() or stat.S_IMODE(s.st_mode) != 0o700:
            raise PurgePending("untrusted_dataset_permissions")
        before = inventory(child_fd, names)
        # Preflight every object BEFORE a handler that otherwise follows paths.
        await official_delete()
        if checkpoint:
            checkpoint("after_official")
        current_dir = os.stat(entry.owner_id, dir_fd=root_fd, follow_symlinks=False)
        if (current_dir.st_dev, current_dir.st_ino) != (s.st_dev, s.st_ino):
            raise PurgePending("dataset_directory_changed")
        after = inventory(child_fd, names)
        for name, signature in after.items():
            if before.get(name) != signature:
                raise PurgePending("artifact_changed")
            latest = os.stat(name, dir_fd=child_fd, follow_symlinks=False)
            if (latest.st_dev, latest.st_ino, latest.st_size,
                    latest.st_mtime_ns, latest.st_ctime_ns) != signature:
                raise PurgePending("artifact_changed")
            os.unlink(name, dir_fd=child_fd)
            if checkpoint:
                checkpoint("after_unlink")
        os.fsync(child_fd)
        if os.listdir(child_fd):
            raise PurgePending("postcondition_incomplete")
        # Preserve an empty owner directory: absence of all main/companions is the
        # postcondition; retaining an opaque directory avoids unsafe recursive rm.
        os.fsync(root_fd)
    except PurgePending:
        raise
    except OSError:
        raise PurgePending("filesystem_error") from None
    finally:
        for fd in (child_fd, root_fd):
            if fd is not None:
                os.close(fd)
