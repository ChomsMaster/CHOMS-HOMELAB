#!/usr/bin/env bash
set -euo pipefail
set +x
export RESTIC_PASSWORD_FILE=/etc/choms-backup/restic-password
METRIC_FILE=/var/lib/node_exporter/textfile_collector/choms_restic_backup.prom
LOCK_FILE=/run/lock/choms-restic-backup.lock
MAX_LOGICAL_BYTES=$((25 * 1024 * 1024 * 1024))
initialize_restic() {
  RESTIC_OPTIONS=()
  if test -n "${CHOMS_RESTIC_SFTP_KEY:-}"; then
    test -f "$CHOMS_RESTIC_SFTP_KEY"
    RESTIC_OPTIONS=(
      -o
      "sftp.command=ssh -i $CHOMS_RESTIC_SFTP_KEY -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o IdentitiesOnly=yes -o IdentityAgent=none -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/root/.ssh/choms-restic-known_hosts choms-restic@192.168.1.134 -s sftp"
    )
  fi
  test "$(id -u)" -eq 0
  test "$(stat -Lc '%U:%G:%a' "$RESTIC_PASSWORD_FILE")" = root:root:600
  exec 9>"$LOCK_FILE"
  flock -n 9 || { echo 'ERROR: local backup already active' >&2; exit 75; }
}
run_restic() { command restic "${RESTIC_OPTIONS[@]}" "$@"; }
publish_metric() {
  local status=$1 duration=$2 bytes=$3 timestamp=$4 tmp
  if [[ "$status" = 0 ]]; then
    timestamp=$(previous_metric choms_restic_backup_last_success_unixtime)
  fi
  tmp="${METRIC_FILE}.tmp.$$"
  install -d -m 0755 "${METRIC_FILE%/*}"
  umask 022
  printf 'choms_restic_backup_success %s\nchoms_restic_backup_duration_seconds %s\nchoms_restic_backup_logical_bytes %s\nchoms_restic_backup_last_success_unixtime %s\n' "$status" "$duration" "$bytes" "$timestamp" >"$tmp"
  if [[ ${RESTIC_HOST:-} = choms-node-01 ]]; then
    local protected
    protected=$(previous_metric choms_restic_backup_protected_package_unixtime)
    [[ "$status" != 1 ]] || protected=${PACKAGE_TIMESTAMP:?}
    printf 'choms_restic_backup_execution_unixtime %s\nchoms_restic_backup_package_unixtime %s\nchoms_restic_backup_package_age_seconds %s\nchoms_restic_backup_package_valid %s\nchoms_restic_backup_protected_package_unixtime %s\n' \
      "${start:-0}" "${PACKAGE_TIMESTAMP:-0}" "${PACKAGE_AGE:-0}" "${PACKAGE_VALID:-0}" "$protected" >>"$tmp"
  fi
  chmod 0644 "$tmp"
  mv "$tmp" "$METRIC_FILE"
}
require_below_limit() {
  local logical_bytes=$1
  [[ "$logical_bytes" =~ ^[0-9]+$ ]] || return 1
  test "$logical_bytes" -le "$MAX_LOGICAL_BYTES" || {
    echo "ERROR: logical scope exceeds the authorized 25 GiB limit" >&2
    return 1
  }
}

previous_metric() {
  if [[ -f "$METRIC_FILE" ]]; then
    awk -v key="$1" '$1 == key && $2 ~ /^[0-9]+$/ {value=$2} END {printf "%.0f\n", value+0}' "$METRIC_FILE"
  else
    printf '0\n'
  fi
}

# Only the producer's flat package tree is read. No extraction or data logging.
select_database_package() {
  local result
  PACKAGE_VALID=0 PACKAGE_TIMESTAMP=0 PACKAGE_AGE=0
  result=$(python3 - "$1" "$2" "${3:-}" "${4:-}" <<'PYCODE'
import datetime as dt
import gzip
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import tarfile
import time

def require(ok):
    if not ok:
        raise ValueError()

try:
    root, now = Path(sys.argv[1]), int(sys.argv[2])
    candidates = []
    for p in root.iterdir():
        name = p.name[5:] if p.name.startswith('.tmp-') else p.name
        require(re.fullmatch(r'[0-9]{8}-[0-9]{6}', name))
        stamp = dt.datetime.strptime(name, '%Y%m%d-%H%M%S')
        # Producer uses node-local time. Reject ambiguous DST wall times.
        epochs = {int(time.mktime((*stamp.timetuple()[:8], dst))) for dst in (0, 1)}
        epochs = {e for e in epochs if time.strftime('%Y%m%d-%H%M%S', time.localtime(e)) == name}
        require(len(epochs) == 1)
        epoch = epochs.pop()
        require(epoch <= now)
        candidates.append((epoch, p))
    require(candidates)
    newest = max(e for e, _ in candidates)
    selected = [p for e, p in candidates if e == newest]
    require(len(selected) == 1)
    p = selected[0]
    require(not p.name.startswith('.tmp-') and p.is_dir() and not p.is_symlink())
    if sys.argv[4]:
        # Final identity/freshness check only. Backup reads the private copy,
        # never the mutable publication path. Do not reopen source members.
        require(p.name == sys.argv[4])
        print(str(p), newest, now - newest, sep='\t')
        sys.exit(0)
    source = p
    # Pin the publication directory. No source member is reopened by path after
    # inspection. The runtime always supplies a private tmpfs staging directory.
    root_fd = os.open(str(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    source_fd = os.open(p.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
    os.close(root_fd)
    names = set(os.listdir(source_fd))
    required = {'SHA256SUMS', 'metadata.txt', 'postgres-contents.txt',
                'mariadb-nextcloud.sql.gz', 'redis-validation.txt',
                'redis-dump.rdb', 'kubernetes-runtime.tgz'}
    dumps = {n for n in names if n.startswith('postgres-') and n.endswith('.dump')}
    require(len(dumps) == 1)
    required |= dumps
    require(required <= names <= required | {'k3s-config.tgz'})
    require(all(stat.S_ISREG(os.stat(n, dir_fd=source_fd, follow_symlinks=False).st_mode) for n in names))
    if sys.argv[3]:
        p = Path(sys.argv[3]) / source.name
        p.mkdir(mode=0o700, parents=True, exist_ok=False)
        size = 0
        for name in sorted(names):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=source_fd)
            with os.fdopen(fd, 'rb') as stream, (p/name).open('xb') as output:
                info = os.fstat(stream.fileno())
                require(stat.S_ISREG(info.st_mode) and info.st_dev == os.fstat(source_fd).st_dev)
                os.fchmod(output.fileno(), 0o600)
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    size += len(chunk)
                    require(size <= 25 * 1024**3)
                    output.write(chunk)
        # A concurrent modification is harmless only when the private copy
        # satisfies the complete checksum/structure contract below.
    os.close(source_fd)
    files = {f.name: f for f in p.iterdir()}
    require(all(stat.S_ISREG(f.lstat().st_mode) and f.stat().st_size > 0 for f in files.values()))
    metadata = files['metadata.txt'].read_text()
    config = re.findall(r'^K3s config included: (yes|no)$', metadata, re.M)
    require(len(config) == 1)
    if config == ['yes']:
        required.add('k3s-config.tgz')
    require(set(files) == required)
    manifest = {}
    for line in files['SHA256SUMS'].read_text().splitlines():
        escaped = line.startswith('\\')
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line[1:] if escaped else line)
        require(match is not None)
        digest, name = match.groups()
        if escaped:
            require(re.search(r'\\(?![\\nr])', name) is None)
            name = re.sub(r'\\([\\nr])', lambda m: {'n': '\n', 'r': '\r', '\\': '\\'}[m[1]], name)
        require(name not in manifest)
        manifest[name] = digest
    require(set(manifest) == required - {'SHA256SUMS'})
    for name, digest in manifest.items():
        h = hashlib.sha256()
        with files[name].open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        require(h.hexdigest() == digest)
    created = re.findall(r'^Created: (.+)$', metadata, re.M)
    require(len(created) == 1)
    end = dt.datetime.fromisoformat(created[0])
    require(end.utcoffset() is not None and newest <= end.timestamp() <= now)
    # Freshness is measured from dump start, not completion of a long run.
    with files[next(iter(dumps))].open('rb') as stream:
        require(stream.read(5) == b'PGDMP')
    with files['redis-dump.rdb'].open('rb') as stream:
        require(re.fullmatch(b'REDIS[0-9]{4}', stream.read(9)))
    found = False
    with gzip.open(files['mariadb-nextcloud.sql.gz'], 'rb') as stream:
        for line in stream:
            found |= b'CREATE TABLE' in line
    require(found)
    expected = {'kubernetes-resources.yaml', 'kubernetes-routes.yaml',
                'metallb-resources.yaml', 'certificates.yaml', 'clusterissuers.yaml',
                'nodes.txt', 'kubernetes-version.yaml', 'helm-releases.json'}
    for archive, names in [('kubernetes-runtime.tgz', expected),
                           ('k3s-config.tgz', {'rancher/k3s/config.yaml'})]:
        if archive not in files:
            continue
        with tarfile.open(files[archive], 'r:gz') as tar:
            members = tar.getmembers()
            require(len(members) == len(names) and {m.name for m in members} == names)
            require(all(m.isfile() and m.size > 0 for m in members))
            for member in members:
                with tar.extractfile(member) as stream:
                    while stream.read(1024 * 1024):
                        pass
    require('\t' not in str(p) and '\n' not in str(p))
    print(str(p), newest, now - newest, sep='\t')
except Exception:
    print('ERROR: database package selection/validation failed', file=sys.stderr)
    sys.exit(1)
PYCODE
  ) || return 1
  IFS=$'\t' read -r DATABASE_PACKAGE PACKAGE_TIMESTAMP PACKAGE_AGE <<<"$result"
  [[ "$PACKAGE_AGE" -le 86400 ]] || { echo 'ERROR: database package expired' >&2; return 1; }
  PACKAGE_VALID=1
}

# Measure the union of authorized sources in one pass. A nested mount causes
# failure, rather than silently undercounting content that Restic would read.
measure_scope() {
  python3 - "$@" <<'PYCODE'
import os
import re
import stat
import sys
try:
    mode, *args = sys.argv[1:]
    if mode == 'mixed':
        assert args and len(args) % 2 == 0
        scopes = list(zip(args[::2], args[1::2]))
    else:
        assert args
        scopes = [(mode, path) for path in args]
    # Linux mount metadata only; never enumerate other filesystem contents.
    with open('/proc/self/mountinfo') as stream:
        mounts = {re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), line.split()[4]) for line in stream}
    files_seen, dirs_seen = set(), set()
    def measure(parent, name, path, device, exclude, is_root=False):
        st = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if st.st_dev != device or (not is_root and path in mounts):
            raise ValueError()
        key = (st.st_dev, st.st_ino)
        if stat.S_ISLNK(st.st_mode) or stat.S_ISREG(st.st_mode):
            if key in files_seen:
                return 0
            files_seen.add(key)
            return st.st_size
        if not stat.S_ISDIR(st.st_mode):
            raise ValueError()
        if (key, exclude) in dirs_seen:
            return 0
        dirs_seen.add((key, exclude))
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            actual = os.fstat(fd)
            if (actual.st_dev, actual.st_ino) != key:
                raise ValueError()
            size = 0
            with os.scandir(fd) as entries:
                for entry in entries:
                    if exclude == 'platform' and entry.name == 'data' and entry.is_dir(follow_symlinks=False):
                        continue
                    size += measure(fd, entry.name, os.path.join(path, entry.name), device, exclude)
            return size
        finally:
            os.close(fd)
    total = 0
    for exclude, path in scopes:
        assert exclude in ('none', 'platform')
        # Explicit roots may include the existing scrutiny latest/ alias.
        follow_root = path.endswith('/')
        path = os.path.abspath(path)
        path = (os.path.realpath(path) if follow_root else
                os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path)))
        total += measure(None, path, path, os.lstat(path).st_dev, exclude, True)
    print(total)
except Exception:
    print('ERROR: authorized scope measurement failed', file=sys.stderr)
    sys.exit(1)
PYCODE
}

initialize_restic
