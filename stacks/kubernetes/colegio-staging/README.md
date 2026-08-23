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
