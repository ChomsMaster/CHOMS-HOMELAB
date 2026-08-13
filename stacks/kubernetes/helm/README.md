# Locked Helm releases

This directory contains the reproducible installer for the Helm-managed
components of CHOMS Platform.

## Safety model

The script defaults to `plan`. Planning uses server-side Helm dry-run and hides
rendered Secret contents.

Applying changes requires the explicit `apply` argument.

## Locked releases

| Release | Namespace | Chart | Version |
|---|---|---|---|
| choms-nfs | nfs-provisioner | nfs-subdir-external-provisioner/nfs-subdir-external-provisioner | 4.0.18 |
| cert-manager | cert-manager | jetstack/cert-manager | v1.21.1 |
| traefik-k8s | traefik | traefik/traefik | 41.1.0 |
| choms-monitoring | monitoring | prometheus-community/kube-prometheus-stack | 88.0.1 |
| choms-loki | logging | grafana-community/loki | 18.7.1 |
| choms-alloy | logging | grafana/alloy | 1.11.0 |

## Prerequisites

- A functional Kubernetes cluster.
- `kubectl` configured for the target cluster.
- Helm 3.
- MetalLB installed and configured before Traefik.
- Required Kubernetes Secrets created through the CHOMS secrets bootstrap.

## Validate

From the repository root:

    ./stacks/kubernetes/helm/apply-releases.sh plan

This does not modify the releases.

## Apply

After reviewing the plan:

    ./stacks/kubernetes/helm/apply-releases.sh apply

Every release uses its versioned values from `stacks/kubernetes`.
Application uses `--atomic`, waits for workloads and Jobs, and rolls back a
release automatically when its upgrade fails.

The timeout defaults to 15 minutes and can be overridden:

    HELM_TIMEOUT=25m ./stacks/kubernetes/helm/apply-releases.sh apply
