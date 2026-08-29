# NAS Scrutiny collector

This directory declares the existing collector on `choms-nas`. It preserves
the pinned Scrutiny 0.8.2 collector image, `choms-nas` host identity, six-hour
schedule, startup collection, privileged device access, `/dev` and read-only
udev mounts, bridge networking, and `unless-stopped` restart policy.

The collector sends telemetry through the existing HTTPS route backed by the
`monitoring/scrutiny` Service. It contains no credentials, mounts no Docker
socket, and does not run SMART self-tests.

Validate the effective container and rendered configuration without changing
the NAS:

```bash
./deploy.sh plan
```

Apply only after the plan reports that the endpoint is the sole effective
change:

```bash
./deploy.sh apply
```

The apply path retains the previous container as a stopped rollback until the
normal startup collection publishes the same five identities successfully.
It restores that container automatically if validation fails.
