# CHOMS Platform Roadmap

## Current State

- Three-node K3s cluster operational.
- MetalLB and Traefik Gateway API edge operational.
- Persistent NFS storage integrated.
- Monitoring and centralized logging operational.
- Core workloads represented declaratively.
- Six Helm releases locked and reproducible.
- Secret values excluded from Git.

## Immediate

1. Complete canonical documentation alignment.
2. Verify the final Jellyfin and Threadfin channel reconciliation.
3. Add probes and resource controls to MariaDB and Redis.
4. Implement declarative drift detection.

## Short Term

1. Validate backups for all NFS-backed persistent volumes.
2. Perform controlled restore tests.
3. Document application-level database backup procedures.
4. Review Prometheus retention and storage capacity.
5. Review Loki retention and storage capacity.
6. Add alerts for failed workloads and storage pressure.

## Medium Term

1. Automate platform validation through CI.
2. Add manifest and Helm values policy checks.
3. Introduce scheduled disaster-recovery exercises.
4. Improve workload scheduling and node-affinity policies.
5. Document node replacement and cluster recovery.
6. Evaluate encrypted and off-site backups.

## Long Term

1. Add high-availability control-plane capacity if justified.
2. Improve network segmentation and firewall policy.
3. Evaluate GitOps reconciliation tooling.
4. Add infrastructure provisioning automation.
5. Establish measurable service-level objectives.
6. Expand CHOMS platform services only after recovery is validated.

## Engineering Rule

Reliability, recovery and reproducibility take priority over adding new
services.
