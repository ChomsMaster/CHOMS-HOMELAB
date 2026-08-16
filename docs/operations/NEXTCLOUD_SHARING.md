# Nextcloud Public Sharing

## Policy

CHOMS Platforms permits public download links through Nextcloud with these
mandatory controls:

- Public links are enabled.
- Every public link requires a password.
- Password entry is enabled by default in the sharing interface.
- Links expire after seven days.
- The expiration date cannot be removed.
- Public uploads are disabled.

SMB, NFS and the NAS must not be exposed to the Internet for client file
delivery.

## Reproducible Configuration

The policy is stored in Nextcloud's application configuration and therefore in
the Nextcloud database. The idempotent configuration script is:

    stacks/kubernetes/apps/configure-nextcloud-sharing.sh

The script defaults to a read-only plan:

    ./stacks/kubernetes/apps/configure-nextcloud-sharing.sh

Apply the reviewed plan from a host with cluster-admin `kubectl` access:

    ./stacks/kubernetes/apps/configure-nextcloud-sharing.sh apply

The script refuses to continue unless a running, ready Nextcloud container is
available. It changes only the eight documented `core` application settings
and verifies every value after applying them. Re-running it is safe and results
in zero changes when the policy is already enforced.

## Settings

| Setting | Value |
|---|---|
| `shareapi_enabled` | `yes` |
| `shareapi_allow_links` | `yes` |
| `shareapi_allow_public_upload` | `no` |
| `shareapi_enforce_links_password` | `yes` |
| `shareapi_enable_link_password_by_default` | `yes` |
| `shareapi_default_expire_date` | `yes` |
| `shareapi_expire_after_n_days` | `7` |
| `shareapi_enforce_expire_date` | `yes` |

Nextcloud 31.0.14 reads these settings from the `core` application
configuration. Values are strings, matching Nextcloud's internal comparisons.

## Validation

After applying the policy:

1. Run the script again in `plan` mode and confirm `Planned changes: 0`.
2. Confirm `php occ status` reports an installed instance with maintenance and
   database upgrade flags disabled.
3. Inspect the server capabilities and confirm public-share password and
   expiration enforcement are enabled and public upload is disabled.
4. Audit existing public shares using aggregate counts only; do not print share
   tokens, paths or user data.
5. Create a client delivery link in the Nextcloud UI and verify anonymously
   that it requires a password, has an expiration date no more than seven days
   away, permits download and does not offer upload.
6. Send the link and password through separate channels.

## Rollback

Before the initial enforcement, all eight settings were absent and Nextcloud
used its built-in defaults. To restore that exact state, delete each setting
with `php occ config:app:delete core <setting>` after recording and reviewing
the planned rollback. A database backup or the established Nextcloud snapshot
should be available before rollback when client shares already exist.
