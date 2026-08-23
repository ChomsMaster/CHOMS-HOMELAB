# Colegio María Rosario staging

This directory owns the staged education platform in independent checkpoints.
Checkpoint 1 contains only the namespace, institutional web, Service,
ForwardAuth middleware and HTTPRoute. Moodle and Gibbon are separate later
checkpoints and must not roll back this foundation if they fail.

The web image is fixed to its verified public GHCR digest. It runs without a
ServiceAccount token, privilege escalation, Linux capabilities, host access or
a writable root filesystem. `private-assets-review` is excluded from the image
and public build.

The three staging hosts use the existing platform Certificate and split DNS.
The current Authelia session cookie is intentionally shared across
`chomsmaster.com` as a temporary staging exception. The definitive school
domain requires authentication and cookie isolation scoped to that domain.

Checkpoint 1 rollback deletes only `colegio-maria-rosario-staging` resources
and restores the previous Authelia, split-DNS and Certificate manifests.
Moodle and Gibbon have their own later rollback boundaries.

## Checkpoint 2 — Moodle

Moodle 5.2.2 and MariaDB 11.4 use separate pinned images, PVCs, Services and
runtime Secrets. The assign validation object carries the official Moodle
5.2.2 defaults, including `visible=1`, the authorized grading defaults and
nullable multimarking fields. The fictional course and task persist, and the
real five-minute CronJob has completed successfully.

`colegio-aula.chomsmaster.com` is routed through the existing Authelia
ForwardAuth on both Gateway listeners. Backup and isolated restore validated
the schema, fictional course/task and `moodledata/filedir`. The restore
marker is artificial and operational only; no real user data was introduced.
Gibbon is deployed in its separate declarative checkpoint; its manual installer
remains pending.

## Checkpoint 3 — Gibbon declarativo

Gibbon 30.0.01 uses the pinned bootstrap image, an independent MariaDB and
dedicated database/runtime PVCs plus a runtime-only Secret. Its ClusterIP
Service and `colegio-gestion.chomsmaster.com` HTTPRoute use both Gateway
listeners and the existing Authelia ForwardAuth.

The official web installer is available behind Authelia. This checkpoint stops
there deliberately: the installer is manual, no account or real data exists,
and the writable runtime PVC remains mutable as required by the official
bundle. Checkpoints 1 and 2 are not part of this rollback boundary.
