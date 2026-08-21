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
