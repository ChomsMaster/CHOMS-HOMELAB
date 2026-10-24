# MetalLB

MetalLB is installed using the upstream native manifest rather than Helm.

## Version

- MetalLB: `v0.15.2`
- Installation mode: native manifest
- Network mode: L2
- Address pool: `192.168.1.240/32`

## Upstream artifact

- Source: `https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml`
- Upstream SHA-256: `a1b04c376fb39c93265f551fe23716a3ae6e09b790edb3bf257d3fc784c35a18`

The vendored manifest preserves the upstream resources. The controller and
speaker image references are changed from version tags to the exact image
digests validated in the CHOMS cluster.

## Declarative files

- `metallb-native-v0.15.2.yaml`: namespace, CRDs, RBAC, webhook and workloads.
- `address-pool.yaml`: CHOMS L2 address pool and advertisement.

## Application order

1. Apply `metallb-native-v0.15.2.yaml`.
2. Verify the controller Deployment and speaker DaemonSet.
3. Apply `address-pool.yaml`.

Secrets generated or populated at runtime are not stored with secret data.
