# CHOMS Kubernetes Deployment

## Source of Truth

The Git repository is the desired-state source of truth:

    /home/chomsmaster/projects/choms-homelab

Kubernetes configuration is stored under:

    stacks/kubernetes

Do not treat manually edited runtime resources as permanent configuration.

## Direct Kubernetes Manifests

Before applying a manifest, validate it against the cluster:

    kubectl apply --dry-run=server -f <manifest>

Review the expected changes:

    kubectl diff -f <manifest>

Apply the reviewed manifest:

    kubectl apply -f <manifest>

For workload changes, verify the rollout:

    kubectl rollout status deployment/<name> -n <namespace>

Apply Namespace resources before their namespaced workloads.

## Helm Releases

Six platform releases use locked chart versions and versioned values.

Validate every release without modifying the cluster:

    ./stacks/kubernetes/helm/apply-releases.sh plan

Apply the locked releases only after a successful review:

    ./stacks/kubernetes/helm/apply-releases.sh apply

The apply operation uses atomic upgrades, waits for workloads and rolls back
the affected release automatically if an upgrade fails.

## Kubernetes Secrets

Secret values are generated from the ignored local environment file:

    ./stacks/kubernetes/secrets/apply-secrets.sh

The following file must never be committed:

    stacks/kubernetes/secrets/secrets.env

## Standard Change Flow

1. Confirm that the Git working tree contains no unrelated changes.
2. Modify the smallest required declarative file.
3. Run syntax and server-side validation.
4. Review the Git diff and Kubernetes diff.
5. Apply only the reviewed resources.
6. Verify rollouts, Pods, Services, PVCs and routes.
7. Commit and push the validated desired state.

## Platform Validation

    kubectl get nodes
    kubectl get pods -A
    kubectl get deployment,statefulset,daemonset -A
    kubectl get service -A
    kubectl get pvc -A
    kubectl get gateway,httproute -A
    helm list -A

Expected Traefik LoadBalancer address: `192.168.1.240`.

## Networking Rule

Application workloads should normally use ClusterIP Services. Public and
protected access is routed through Traefik and Kubernetes Gateway API.

Do not introduce NodePort exposure when an application is already reachable
through the platform edge.

## Safety

- Do not delete PVCs during a routine deployment.
- Do not apply floating Helm chart versions.
- Do not commit credentials or rendered Secret values.
- Do not apply runtime exports without cleaning generated fields.
- Do not combine unrelated platform changes in the same deployment.
