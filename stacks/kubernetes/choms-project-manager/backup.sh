#!/usr/bin/env bash
# Run on the backup operator's workstation with a private, encrypted destination.
set -euo pipefail
umask 077
dest=${1:?Especifica un directorio privado de backup}
[[ -d "$dest" ]] || exit 2
name="choms-project-manager-$(date -u +%Y%m%dT%H%M%SZ).dump"
staged=$(mktemp "$dest/.$name.XXXXXX")
trap 'rm -f -- "$staged"' EXIT
kubectl -n choms-project-manager exec project-db-0 -- sh -ec '
  PGPASSWORD="$CAREER_DB_PASSWORD" pg_dump -h 127.0.0.1 -U career -Fc career
' >"$staged"
test -s "$staged"
kubectl -n choms-project-manager exec -i project-db-0 -- pg_restore --list <"$staged" >/dev/null
ln -- "$staged" "$dest/$name"
(
  cd -- "$dest"
  set -o noclobber
  sha256sum "$name" >"$name.sha256"
)
printf '%s\n' "$dest/$name"
