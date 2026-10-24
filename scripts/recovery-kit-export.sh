#!/usr/bin/env bash
# Offline exporter: consumes an operator-prepared allowlist, never queries hosts.
# Parse/lint in CI only. Do not run this script during repository maintenance.
set +x
set -euo pipefail
umask 077
ulimit -c 0

fail() { printf '%s\n' "$1" >&2; exit 1; }
[[ $# -eq 1 ]] || fail 'Usage: recovery-kit-export.sh EXTERNAL_INPUT_DIRECTORY'
[[ -n ${SOPS_AGE_KEY_FILE:-} ]] || fail 'Required external age identity is missing.'
for tool in age-keygen sops python3 git realpath stat mktemp; do
  command -v "$tool" >/dev/null 2>&1 || fail 'A required local tool is missing.'
done

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
destination="$repo_root/../choms-recovery-private"
[[ -d $destination && ! -L $destination ]] || fail 'The approved private repository must already exist.'
destination="$(realpath -e -- "$destination" 2>/dev/null)" || fail 'Invalid destination.'
[[ -d $1 && ! -L $1 ]] || fail 'Input must be a real external directory.'
input_dir="$(realpath -e -- "$1" 2>/dev/null)" || fail 'Invalid input directory.'
[[ -f $SOPS_AGE_KEY_FILE && ! -L $SOPS_AGE_KEY_FILE ]] || fail 'age identity must be a regular non-symlink file.'
identity_file="$(realpath -e -- "$SOPS_AGE_KEY_FILE" 2>/dev/null)" || fail 'Invalid age identity.'
for external_path in "$input_dir" "$identity_file"; do
  case "$external_path" in
    "$repo_root"|"$repo_root"/*|"$destination"|"$destination"/*)
      fail 'Inputs and identity must stay outside both repositories.' ;;
  esac
done
case "$identity_file" in "$input_dir"/*) fail 'Store the identity separately from recovery inputs.' ;; esac
[[ $(stat -c '%u:%a' -- "$identity_file") == "$EUID:600" ]] || fail 'age identity must be owned by the operator with mode 0600.'
[[ $(stat -c '%u:%a' -- "$input_dir") == "$EUID:700" ]] || fail 'Input directory must be owned by the operator with mode 0700.'
export SOPS_AGE_KEY_FILE="$identity_file"
# Only the public recipient enters command arguments. No identity or payload is echoed.
age_recipient="$(age-keygen -y "$identity_file" 2>/dev/null)" || fail 'Cannot read the age identity.'
[[ $age_recipient == age1* && $age_recipient != *$'\n'* ]] || fail 'Unsupported age identity.'
[[ $(git -C "$destination" rev-parse --show-toplevel 2>/dev/null) == "$destination" ]] || fail 'Destination must be its own Git worktree.'
[[ $(git -C "$destination" config --local --get choms.recoveryPrivateApproved || true) == true ]] || fail 'Operator private-repository approval is required.'

# Audit tracked PATHS only. Visibility cannot be proven offline; no remote access.
git -C "$destination" ls-files -z | python3 -c '
import re, sys
names = sys.stdin.buffer.read().decode().split("\0")
allowed = re.compile(r"kits/[A-Za-z0-9._-]+/[a-z0-9-]+[.]enc[.]json")
sys.exit(0 if all(not n or n == ".gitignore" or allowed.fullmatch(n) for n in names) else 1)
' || fail 'Destination tracks files outside the encrypted-only contract.'

required=(kubernetes-secrets.json k3s-token k3s-snapshot k3s-snapshot-meta.json
          authelia-configuration.yml restic-password ansible-vars.yml network-dns.md)
optional=(authelia-users.yml k3s-encryption-config.json)
sources=("${required[@]}")
for name in "${optional[@]}"; do
  [[ ! -e $input_dir/$name ]] || sources+=("$name")
done
for name in "${sources[@]}"; do
  source_file="$input_dir/$name"
  [[ -f $source_file && ! -L $source_file && -s $source_file ]] || fail 'A required input is absent, empty or not a regular file.'
  [[ $(stat -c '%u:%a' -- "$source_file") == "$EUID:600" ]] || fail 'Inputs must be owned by the operator with mode 0600.'
done
# Suppress parser errors: no values, paths, secret names or configuration reach logs.
python3 - "$input_dir" 2>/dev/null <<'PY' || fail 'Input contract validation failed.'
from pathlib import Path
import json
import sys
root = Path(sys.argv[1])
secrets = json.loads((root / 'kubernetes-secrets.json').read_bytes())
assert secrets.get('kind') in ('List', 'SecretList')
assert isinstance(secrets.get('items'), list) and secrets['items']
assert all(item.get('kind') == 'Secret' for item in secrets['items'])
meta = json.loads((root / 'k3s-snapshot-meta.json').read_bytes())
assert meta['datastore'] in ('sqlite', 'etcd')
assert meta['consistency'] in ('offline', 'sqlite-backup-api', 'etcd-snapshot')
assert isinstance(meta['k3s_version'], str) and meta['k3s_version']
assert isinstance(meta['secrets_encryption'], bool)
assert (root / 'k3s-encryption-config.json').is_file() or not meta['secrets_encryption']
assert meta['datastore'] != 'sqlite' or meta['consistency'] in ('offline', 'sqlite-backup-api')
assert meta['datastore'] != 'etcd' or meta['consistency'] == 'etcd-snapshot'
if meta['datastore'] == 'sqlite':
    with (root / 'k3s-snapshot').open('rb') as stream:
        assert stream.read(16) == b'SQLite format 3\0'
else:
    assert (root / 'k3s-snapshot').stat().st_size > 0
for file in root.iterdir():
    if file.name == 'k3s-snapshot':
        assert file.stat().st_size <= 512 * 1024 * 1024
    elif file.name == 'kubernetes-secrets.json':
        assert file.stat().st_size <= 32 * 1024 * 1024
    elif file.name in {'k3s-token', 'k3s-snapshot-meta.json', 'authelia-configuration.yml',
                       'restic-password', 'ansible-vars.yml', 'network-dns.md',
                       'authelia-users.yml', 'k3s-encryption-config.json'}:
        assert file.stat().st_size <= 4 * 1024 * 1024
PY

[[ ! -L $destination/.gitignore ]] || fail 'Refusing a symlink guard file.'
[[ ! -L $destination/kits ]] || fail 'Refusing a symlink kit directory.'
# Last matching rules win; only ciphertext and the guard file may become tracked.
cat >> "$destination/.gitignore" <<'GUARDS'

# Recovery kit: deny by default. Never force-add plaintext.
/*
!/.gitignore
!/kits/
/kits/*
!/kits/*/
/kits/*/*
!/kits/*/*.enc.json
GUARDS
mkdir -p -- "$destination/kits"
work_dir="$(mktemp -d "$destination/.pending.XXXXXXXX")"
trap 'rm -rf -- "$work_dir"' EXIT
for name in "${sources[@]}"; do
  safe_name="${name//./-}"
  # binary input protects every byte, including config keys and comments.
  if ! cat -- "$input_dir/$name" 2>/dev/null |
    sops --encrypt --age "$age_recipient" --input-type binary --output-type json \
      --filename-override "$safe_name.enc.json" /dev/stdin \
      > "$work_dir/$safe_name.enc.json" 2>/dev/null; then
    fail 'Encryption failed; no kit has been published.'
  fi
done
kit_name="$(date -u +%Y%m%dT%H%M%SZ)-${work_dir##*.}"
mv -- "$work_dir" "$destination/kits/$kit_name"
printf '%s\n' 'Encrypted recovery kit prepared. No commit or push performed.'
