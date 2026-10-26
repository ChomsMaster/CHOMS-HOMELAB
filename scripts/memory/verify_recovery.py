#!/usr/bin/env python3
"""Read-only integrity gate for a decrypted Cognee restore in root-only tmpfs.

This does not collect live data, decrypt, publish a backup, or prove restoration.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ARTIFACTS = frozenset({
    'relational.dump', 'vectors.dump', 'graph-export.tar', 'documents.tar',
    'models.tar', 'declarative.tar', 'image.oci.tar',
})
MAX_BYTES = 25 * 1024**3


class VerificationError(Exception):
    pass


def require(ok, reason):
    if not ok:
        raise VerificationError(reason)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate_manifest_key')
        value[key] = item
    return value


def manifest(raw, expected):
    require(re.fullmatch(r'[0-9a-f]{64}', expected) is not None, 'manifest_hash_format')
    require(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == expected,
            'manifest_hash_mismatch')
    try:
        value = json.loads(raw, object_pairs_hook=unique_object)
        require(set(value) == {'schema', 'captured_at', 'source_commit', 'counts', 'artifacts'},
                'manifest_fields')
        require(value['schema'] == 'choms-cognee-recovery-v1', 'manifest_schema')
        stamp = datetime.datetime.fromisoformat(value['captured_at'])
        require(stamp.utcoffset() == datetime.timedelta(0), 'timestamp_not_utc')
        require(re.fullmatch(r'[0-9a-f]{40}', value['source_commit']) is not None,
                'source_commit_format')
        require(value['counts'] == {'documents': 36, 'nodes': 2226, 'edges': 6040},
                'source_counts_mismatch')
        require(set(value['artifacts']) == ARTIFACTS, 'artifact_set_mismatch')
        total = 0
        for info in value['artifacts'].values():
            require(set(info) == {'bytes', 'sha256'}, 'artifact_fields')
            require(type(info['bytes']) is int and info['bytes'] > 0, 'artifact_size')
            require(re.fullmatch(r'[0-9a-f]{64}', info['sha256']) is not None,
                    'artifact_hash_format')
            total += info['bytes']
        require(total <= MAX_BYTES, 'scope_exceeds_25GiB')
    except (ValueError, TypeError, KeyError, AttributeError):
        raise VerificationError('invalid_manifest') from None
    return value


def verify_streams(raw, expected, streams):
    value = manifest(raw, expected)
    require(set(streams) == ARTIFACTS, 'missing_or_unexpected_artifact')
    for name, stream in streams.items():
        digest = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(chunk)
            require(size <= value['artifacts'][name]['bytes'], 'artifact_size_mismatch')
            digest.update(chunk)
        require(size == value['artifacts'][name]['bytes'], 'artifact_size_mismatch')
        require(digest.hexdigest() == value['artifacts'][name]['sha256'],
                'artifact_checksum_mismatch')
    return value


def verify_directory(path, expected):
    require(os.geteuid() == 0, 'root_required')
    path = Path(path)
    require(path.parent == Path('/run') and
            re.fullmatch(r'choms-cognee-restore\.[A-Za-z0-9_-]+', path.name),
            'unexpected_restore_directory')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and info.st_gid == 0
            and stat.S_IMODE(info.st_mode) == 0o700, 'directory_not_root_private')
    fs = subprocess.run(['stat', '-f', '-c', '%T', str(path)], capture_output=True,
                        text=True, check=True)
    require(fs.stdout.strip() == 'tmpfs', 'plaintext_requires_tmpfs')
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    handles = {}
    snapshots = {}
    try:
        require(set(os.listdir(directory)) == ARTIFACTS | {'manifest.json', 'SHA256SUMS'},
                'missing_or_unexpected_artifact')
        for name in ARTIFACTS | {'manifest.json', 'SHA256SUMS'}:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
            handle = os.fdopen(fd, 'rb')
            handles[name] = handle
            st = os.fstat(fd)
            require(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and st.st_gid == 0
                    and stat.S_IMODE(st.st_mode) == 0o600 and st.st_nlink == 1,
                    'member_not_root_private_regular')
            snapshots[name] = st
        raw = handles['manifest.json'].read(65537)
        value = manifest(raw, expected)
        sums = {name: info['sha256'] for name, info in value['artifacts'].items()}
        sums['manifest.json'] = expected
        canonical = ''.join(sums[name] + '  ' + name + '\n' for name in sorted(sums))
        require(handles['SHA256SUMS'].read(65537) == canonical.encode(),
                'checksum_manifest_mismatch')
        verify_streams(raw, expected, {name: handles[name] for name in ARTIFACTS})
        for name, handle in handles.items():
            current = os.fstat(handle.fileno())
            original = snapshots[name]
            require((current.st_ino, current.st_dev, current.st_size,
                     current.st_mtime_ns, current.st_ctime_ns) ==
                    (original.st_ino, original.st_dev, original.st_size,
                     original.st_mtime_ns, original.st_ctime_ns), 'member_changed_during_read')
        return value
    finally:
        for handle in handles.values():
            handle.close()
        os.close(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    try:
        verify_directory(args.directory, args.manifest_sha256)
    except VerificationError as error:
        print('CHECK_FAIL cognee_recovery_integrity reason=' + str(error))
        return 1
    except Exception:
        print('CHECK_FAIL cognee_recovery_integrity reason=io_or_metadata_error')
        return 1
    print('CHECK_PASS cognee_recovery_integrity')
    return 0


if __name__ == '__main__':
    sys.exit(main())
