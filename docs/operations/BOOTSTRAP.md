# CHOMS Kubernetes Bootstrap

## Purpose

This procedure reconstructs CHOMS workloads on an existing functional K3s
cluster. It does not install Debian, K3s or the NAS.

Run commands from the repository root with kubectl and Helm configured for
the target cluster.

## Prerequisites

- All three K3s nodes are Ready.
- Helm 3 is installed.
- NAS `192.168.1.167` exports `/srv/storage/kubernetes`.
- DNS and network connectivity are functional.
- Local `stacks/kubernetes/secrets/secrets.env` exists with mode `600`.

## Bootstrap Order

### 1. MetalLB

Apply the vendored native installation:

    kubectl apply -f stacks/kubernetes/metallb/metallb-native-v0.15.2.yaml
    kubectl rollout status deployment/controller -n metallb-system
    kubectl rollout status daemonset/speaker -n metallb-system
    kubectl apply -f stacks/kubernetes/metallb/address-pool.yaml

### 2. Kubernetes Secrets

Generate Secrets from the ignored local environment file:

    ./stacks/kubernetes/secrets/apply-secrets.sh

Never commit `stacks/kubernetes/secrets/secrets.env`.

### 3. Locked Helm Releases

Validate first:

    ./stacks/kubernetes/helm/apply-releases.sh plan

Apply only after reviewing the successful plan:

    ./stacks/kubernetes/helm/apply-releases.sh apply

### 4. Direct Manifests

Apply namespaces before namespaced resources. Validate every manifest before
applying it:

    kubectl apply --dry-run=server -f <manifest>
    kubectl diff -f <manifest>
    kubectl apply -f <manifest>

Direct manifests are stored under `stacks/kubernetes`.

### 5. Validation

    kubectl get nodes
    kubectl get pods -A
    kubectl get pvc -A
    kubectl get gateway,httproute -A
    helm list -A

Expected Traefik edge address: `192.168.1.240`.

## Safety

- Do not delete PVCs during routine deployment.
- Do not apply unreviewed chart upgrades.
- Do not commit Secret values.
- Do not use runtime exports as desired state without cleaning them.
