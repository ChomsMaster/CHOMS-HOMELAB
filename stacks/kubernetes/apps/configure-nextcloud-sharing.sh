#!/bin/bash
set -euo pipefail

MODE="${1:-plan}"
NAMESPACE="${NEXTCLOUD_NAMESPACE:-apps}"
SELECTOR="${NEXTCLOUD_SELECTOR:-app=nextcloud}"
KUBECTL="${KUBECTL:-kubectl}"

case "$MODE" in
  plan|apply)
    ;;
  *)
    echo "Usage: $0 [plan|apply]" >&2
    exit 2
    ;;
esac

pod="$($KUBECTL get pod \
  -n "$NAMESPACE" \
  -l "$SELECTOR" \
  --field-selector=status.phase=Running \
  -o jsonpath='{.items[0].metadata.name}')"

if [[ -z "$pod" ]]; then
  echo "ERROR: no running Nextcloud Pod found" >&2
  exit 1
fi

ready="$($KUBECTL get pod "$pod" -n "$NAMESPACE" \
  -o jsonpath='{.status.containerStatuses[?(@.name=="nextcloud")].ready}')"

if [[ "$ready" != "true" ]]; then
  echo "ERROR: Nextcloud container is not ready" >&2
  exit 1
fi

keys=(
  shareapi_enabled
  shareapi_allow_links
  shareapi_allow_public_upload
  shareapi_enforce_links_password
  shareapi_enable_link_password_by_default
  shareapi_default_expire_date
  shareapi_expire_after_n_days
  shareapi_enforce_expire_date
)

values=(
  yes
  yes
  no
  yes
  yes
  yes
  7
  yes
)

get_value() {
  $KUBECTL exec -n "$NAMESPACE" "$pod" -c nextcloud -- \
    php occ config:app:get core "$1" 2>/dev/null || true
}

echo "Nextcloud Pod: $pod"
echo "Mode: $MODE"
echo
printf '%-45s %-16s %s\n' "KEY" "CURRENT" "DESIRED"

changes=0
for index in "${!keys[@]}"; do
  key="${keys[$index]}"
  desired="${values[$index]}"
  current="$(get_value "$key")"

  printf '%-45s %-16s %s\n' \
    "$key" "${current:-[default]}" "$desired"

  if [[ "$current" != "$desired" ]]; then
    changes=$((changes + 1))
    if [[ "$MODE" == "apply" ]]; then
      $KUBECTL exec -n "$NAMESPACE" "$pod" -c nextcloud -- \
        php occ config:app:set core "$key" \
          --value="$desired" \
          --type=string \
          --no-interaction
    fi
  fi
done

if [[ "$MODE" == "plan" ]]; then
  echo
  echo "Planned changes: $changes"
  echo "Re-run this script with the 'apply' argument to enforce the policy."
  exit 0
fi

echo
echo "Verifying applied policy"
for index in "${!keys[@]}"; do
  key="${keys[$index]}"
  desired="${values[$index]}"
  current="$(get_value "$key")"

  if [[ "$current" != "$desired" ]]; then
    echo "ERROR: $key is '$current', expected '$desired'" >&2
    exit 1
  fi
done

echo "Nextcloud public-sharing policy is enforced."
