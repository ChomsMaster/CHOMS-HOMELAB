#!/usr/bin/env bash
set -euo pipefail
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# Load production functions, omitting only privileged initialization.
# Mount metadata is synthetic too; do not inspect this machine's mounts.
: >"$work/mountinfo"
sed -e '/^initialize_restic$/d' -e "s|/proc/self/mountinfo|$work/mountinfo|" \
  "$root/scripts/choms-restic-common.sh" >"$work/common.sh"
# shellcheck source=/dev/null
source "$work/common.sh"
export TZ=UTC
now=1790164800
python3 - "$work" "$now" <<'PY'
from pathlib import Path
import datetime as dt
import gzip
import hashlib
import io
import sys
import tarfile
root, now = Path(sys.argv[1]), int(sys.argv[2])
def package(case, age=60, broken=None):
    epoch = now-age
    name = dt.datetime.fromtimestamp(epoch, dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
    p = root/case/name
    p.mkdir(parents=True)
    files = {'postgres-synthetic.dump': b'PGDMPsynthetic',
             'postgres-contents.txt': b'synthetic list',
             'redis-dump.rdb': b'REDIS0011synthetic',
             'redis-validation.txt': b'synthetic validation',
             'metadata.txt': ('Created: '+dt.datetime.fromtimestamp(epoch+1, dt.timezone.utc).isoformat()+'\nK3s config included: no\n').encode()}
    files['mariadb-nextcloud.sql.gz'] = gzip.compress(b'CREATE TABLE synthetic;\n')
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name in ('kubernetes-resources.yaml', 'kubernetes-routes.yaml', 'metallb-resources.yaml',
                     'certificates.yaml', 'clusterissuers.yaml', 'nodes.txt',
                     'kubernetes-version.yaml', 'helm-releases.json'):
            info = tarfile.TarInfo(name); info.size = 9
            tar.addfile(info, io.BytesIO(b'synthetic'))
    files['kubernetes-runtime.tgz'] = buffer.getvalue()
    if broken in ('config', 'archive'):
        files['metadata.txt'] = files['metadata.txt'].replace(b'included: no', b'included: yes')
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
            info = tarfile.TarInfo('rancher/k3s/config.yaml' if broken == 'config' else '../escape')
            info.size = 9
            tar.addfile(info, io.BytesIO(b'synthetic'))
        files['k3s-config.tgz'] = buffer.getvalue()
    if broken == 'structure':
        del files['redis-validation.txt']
    if broken == 'created':
        files['metadata.txt'] = b'Created: invalid\nK3s config included: no\n'
    for name, data in files.items():
        (p/name).write_bytes(data)
    (p/'SHA256SUMS').write_text(''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in files.items()))
    if broken == 'checksum':
        (p/'redis-dump.rdb').write_bytes(b'REDIS0011changed')
    return p
package('fresh')
package('spaced')
p = root/'spaced'/dt.datetime.fromtimestamp(now-60, dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
(p/'postgres-synthetic.dump').rename(p/'postgres-synthetic database.dump')
m = p/'SHA256SUMS'; m.write_text(m.read_text().replace('postgres-synthetic.dump', 'postgres-synthetic database.dump'))
package('config', broken='config')
package('archive', broken='archive')
p = package('unpublished'); (p/'SHA256SUMS').unlink()
package('multiple', 120); package('multiple')
package('incomplete', 120)
p = package('incomplete'); p.rename(p.with_name('.tmp-'+p.name))
for case in ('checksum', 'structure', 'created'):
    package(case, 120); package(case, broken=case)
package('expired', 86401)
package('boundary', 86400)
(root/'empty').mkdir()
(root/'invalid'/'20261399-999999').mkdir(parents=True)
p = package('ambiguous'); (p.parent/('.tmp-'+p.name)).mkdir()
package('future', -60)
p = package('symlink'); (p/'metadata.txt').unlink(); (p/'metadata.txt').symlink_to(root/'missing')
(root/'scope'/'data').mkdir(parents=True)
(root/'scope'/'allowed').write_bytes(b'12345')
(root/'scope'/'data'/'excluded').write_bytes(b'excluded')
with (root/'large').open('wb') as f:
    f.truncate(25*1024**3+1)
PY
pass=0
ok() { pass=$((pass+1)); }
select_database_package "$work/fresh" "$now"
[[ $PACKAGE_VALID = 1 && $PACKAGE_AGE = 60 && $PACKAGE_TIMESTAMP = $((now-60)) ]]; ok
select_database_package "$work/multiple" "$now"
[[ $PACKAGE_TIMESTAMP = $((now-60)) ]]; ok
select_database_package "$work/boundary" "$now"; ok
select_database_package "$work/config" "$now"; ok
select_database_package "$work/spaced" "$now"; ok
# Restic consumes a private, validated copy; replacement of the source cannot
# change those bytes. All generated data stays within this fixture directory.
(umask 077; select_database_package "$work/spaced" "$now" "$work/staged")
python3 - "$work" <<'PYCODE'
from pathlib import Path
import hashlib
import sys
root = Path(sys.argv[1])
source = next((root/'spaced').iterdir())
staged = next((root/'staged').iterdir())
name = 'postgres-synthetic database.dump'
expected = hashlib.sha256((staged/name).read_bytes()).digest()
(source/name).unlink()
(source/name).symlink_to(root/'large')
assert hashlib.sha256((staged/name).read_bytes()).digest() == expected
assert staged.stat().st_mode & 0o777 == 0o700
assert all(p.stat().st_mode & 0o777 == 0o600 for p in staged.iterdir())
PYCODE
ok
for case in incomplete checksum structure created expired empty invalid ambiguous future symlink archive unpublished; do
  if select_database_package "$work/$case" "$now" 2>"$work/error"; then
    echo "ERROR: accepted synthetic case $case" >&2; exit 1
  fi
  [[ $PACKAGE_VALID = 0 ]]
  # Errors contain no fixture names, member names or data.
  ! grep -Fq "$work" "$work/error"
  ok
done
bytes=$(measure_scope platform "$work/scope")
[[ $bytes = 5 ]]; require_below_limit "$bytes"; ok
[[ $(measure_scope none "$work/scope") = 13 ]]; ok
[[ $(measure_scope mixed platform "$work/scope" none "$work/scope/allowed") = 5 ]]; ok
[[ $(measure_scope mixed platform "$work/scope" none "$work/scope") = 13 ]]; ok
# Synthetic same-device bind mount: reject before descending, without mounting.
printf '1 0 0:1 / %s rw - tmpfs tmpfs rw\n' "$work/scope/data" >"$work/mountinfo"
if measure_scope none "$work/scope" >"$work/result" 2>"$work/error"; then exit 1; fi
[[ ! -s "$work/result" ]]; ok
[[ $(measure_scope platform "$work/scope") = 5 ]]; ok
: >"$work/mountinfo"
bytes=$(measure_scope none "$work/large")
[[ $bytes = $((MAX_LOGICAL_BYTES+1)) ]]
if require_below_limit "$bytes" 2>"$work/error"; then exit 1; fi; ok
require_below_limit "$MAX_LOGICAL_BYTES"; ok
if measure_scope none "$work/missing" >"$work/result" 2>"$work/error"; then exit 1; fi
[[ ! -s "$work/result" ]]; ok
if require_below_limit -1; then exit 1; fi; ok
METRIC_FILE=$work/metrics/backup.prom
export RESTIC_HOST=choms-node-01
start=$now
select_database_package "$work/fresh" "$now"
publish_metric 1 3 5 "$now"
[[ $(previous_metric choms_restic_backup_last_success_unixtime) = "$now" ]]
[[ $(previous_metric choms_restic_backup_protected_package_unixtime) = "$((now-60))" ]]; ok
select_database_package "$work/expired" "$now" 2>"$work/error" && exit 1
publish_metric 0 2 0 0
[[ $(previous_metric choms_restic_backup_success) = 0 ]]
[[ $(previous_metric choms_restic_backup_last_success_unixtime) = "$now" ]]
[[ $(previous_metric choms_restic_backup_protected_package_unixtime) = "$((now-60))" ]]
[[ $(previous_metric choms_restic_backup_package_unixtime) = "$((now-86401))" ]]
[[ $(previous_metric choms_restic_backup_package_age_seconds) = 86401 ]]
[[ $(previous_metric choms_restic_backup_package_valid) = 0 ]]; ok
publish_metric 0 2 0 0
[[ $(previous_metric choms_restic_backup_last_success_unixtime) = "$now" ]]; ok
METRIC_FILE=$work/metrics/first-failure.prom
publish_metric 0 2 0 0
[[ $(previous_metric choms_restic_backup_last_success_unixtime) = 0 ]]; ok
# Gate integration: failed selection/measurement must prevent the backup call.
for case in incomplete checksum structure created expired empty invalid ambiguous; do
  marker=$work/restic-called
  if bash -c 'source "$1"; select_database_package "$2" "$3"; touch "$4"' \
      bash "$work/common.sh" "$work/$case" "$now" "$marker" 2>"$work/error"; then exit 1; fi
  [[ ! -e "$marker" ]]; ok
done
# Exercise the actual node-01 script with synthetic paths and command doubles.
# No production source, credentials, executable Restic, or API is accessed.
python3 - "$root" "$work" <<'PYCODE'
from pathlib import Path
import re
import sqlite3
import sys
root, work = map(Path, sys.argv[1:])
s = (root/'scripts/choms-restic-backup-node01.sh').read_text()
s = s.replace('source /usr/local/lib/choms-restic-common.sh', 'source "'+str(work/'integration-common.sh')+'"')
s = s.replace('/data/backups/kubernetes', '${FIXTURE_PACKAGE_ROOT}')
for prefix in ('/var/lib/rancher', '/etc/rancher', '/etc/choms-backup', '/mnt/choms-storage', '/mnt/choms-backups', '/run'):
    s = s.replace(prefix, str(work/'node')+prefix)
(work/'node.sh').write_text(s)
for path in re.findall(re.escape(str(work/'node'))+r'[^\s";)]+', s):
    if '$' in path or path.endswith(('state.db', 'token', '.txt', '.yaml')) or '/etcd/' in path or 'XXXXXX' in path:
        continue
    Path(path).mkdir(parents=True, exist_ok=True)
for rel in ('var/lib/rancher/k3s/server/token', 'etc/choms-backup/recovery-sample.txt'):
    p = work/'node'/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('synthetic')
p = work/'node/var/lib/rancher/k3s/server/db/state.db'
p.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(p) as conn:
    conn.execute('create table synthetic (id integer)')
# The array adds these Nextcloud subdirectories dynamically.
for p in (work/'node/mnt/choms-storage/kubernetes').glob('apps-nextcloud-*'):
    for name in ('config', 'custom_apps', 'themes'):
        (p/name).mkdir()
PYCODE
cat "$work/common.sh" >"$work/integration-common.sh"
cat >>"$work/integration-common.sh" <<'MOCKS'
METRIC_FILE=$FIXTURE_WORK/integration.prom
stat() {
  if [[ "$*" = "-f -c %T $FIXTURE_WORK/node/run" ]]; then
    printf 'tmpfs\n'
  elif [[ "$1" = -c && "$2" = '%u:%a' ]]; then
    [[ $(command stat -c %a "$3") = 700 ]] || return 1
    printf '0:700\n'
  else
    command stat "$@"
  fi
}
date() { printf '%s\n' "$FIXTURE_NOW"; }
kubectl() { printf '{"items":[]}\n'; }
jq() { cat; }
run_restic() {
  printf 'called\n' >>"$FIXTURE_WORK/calls"
  [[ " $* " != *' --stdin '* ]] || cat >/dev/null
  if [[ -n ${FIXTURE_SIGNAL:-} ]]; then kill -s "$FIXTURE_SIGNAL" "$$"; fi
  [[ ${FIXTURE_RESTIC_FAIL:-0} = 0 ]]
}
MOCKS
export FIXTURE_WORK=$work FIXTURE_NOW=$now
for case in fresh expired incomplete checksum structure created empty invalid ambiguous; do
  export FIXTURE_PACKAGE_ROOT=$work/$case
  rm -f "$work/calls"
  if bash "$work/node.sh" >"$work/output" 2>"$work/error"; then
    [[ $case = fresh && $(wc -l <"$work/calls") = 4 ]]
  else
    [[ $case != fresh && ! -e "$work/calls" ]]
  fi
  [[ -z $(find "$work/node/run" -mindepth 1 -maxdepth 1 -print -quit) ]]
  ok
done
# The successful first run survives every later preflight failure.
METRIC_FILE=$work/integration.prom
[[ $(previous_metric choms_restic_backup_last_success_unixtime) = "$now" ]]; ok
export FIXTURE_PACKAGE_ROOT=$work/fresh FIXTURE_RESTIC_FAIL=1
rm -f "$work/calls"
if bash "$work/node.sh" >"$work/output" 2>"$work/error"; then exit 1; fi
[[ $(wc -l <"$work/calls") = 1 ]]
[[ $(previous_metric choms_restic_backup_success) = 0 ]]
[[ $(previous_metric choms_restic_backup_last_success_unixtime) = "$now" ]]; ok
export FIXTURE_RESTIC_FAIL=0
for signal in INT TERM HUP; do
  export FIXTURE_SIGNAL=$signal
  if bash "$work/node.sh" >"$work/output" 2>"$work/error"; then exit 1; fi
  [[ -z $(find "$work/node/run" -mindepth 1 -maxdepth 1 -print -quit) ]]
  [[ $(previous_metric choms_restic_backup_last_success_unixtime) = "$now" ]]
  [[ $(previous_metric choms_restic_backup_protected_package_unixtime) = "$((now-60))" ]]; ok
done
unset FIXTURE_SIGNAL
# Oversized and missing authorized paths fail before any Restic invocation.
scope_file=$work/node/etc/choms-backup/recovery-sample.txt
cp --sparse=always "$work/large" "$scope_file"
rm -f "$work/calls"
if bash "$work/node.sh" >"$work/output" 2>"$work/error"; then exit 1; fi
[[ ! -e "$work/calls" ]]; ok
rm "$scope_file"
if bash "$work/node.sh" >"$work/output" 2>"$work/error"; then exit 1; fi
[[ ! -e "$work/calls" ]]; ok
printf 'node01_synthetic_checks=%s passed\n' "$pass"
