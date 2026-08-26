# Runtime Secret contracts

Secret values are never stored in Git. The bootstrap script in this directory
manages only the environment-backed application Secrets documented by its
example file. Runtime-generated credentials have separate lifecycle owners.

## Scrutiny InfluxDB backup authorization

- Object: `monitoring/scrutiny-backup-influx-operator`
- Type: `Opaque`
- Required keys: `token`, `authorization-id`
- Owner: the Scrutiny official backup/restore workflow
- Creation: one-time, offline `influxd recovery auth create-operator` with a
  closed stdin pipeline
- Revocation order: delete the InfluxDB authorization using its own token,
  prove that token no longer authenticates, then delete the Secret

Do not add these values to `secrets.env`, `secrets.env.example`, manifests,
arguments, logs, backup metadata or documentation. A future backup consumer
must reference the keys with `secretKeyRef`; it must not copy or transform the
credential into another persisted object.

## Alertmanager Telegram configuration

- Object: `monitoring/choms-monitoring-alertmanager-config`
- Type: `Opaque`
- Required keys: `alertmanager.yaml`, `telegram-bot-token`
- Owner: the external Alertmanager Telegram bootstrap workflow

This Secret is external to Git. Neither the Telegram bot token nor the
`chat_id` belongs in versioned values, manifests, environment files, command
arguments, logs or documentation. Create or reconcile it interactively from
the repository root:

    ./stacks/kubernetes/monitoring/apply-alertmanager-telegram-secret.sh

The script reads both values without echo, holds them only in mode-0600
temporary files, removes those files on exit, and uses server-side apply over
stdin. Run the locked monitoring Helm workflow separately only after reviewing
its plan.

To rotate the bot token, revoke the old token with BotFather, obtain the new
token, rerun the same script with the existing `chat_id`, and then perform the
separately authorized monitoring Helm validation and rollout checks. Do not
delete or edit the Secret manually, and do not send a test notification unless
that action is explicitly authorized.
