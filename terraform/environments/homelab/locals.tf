locals {
  # The four built-in Kubernetes namespaces retain K3s ownership.
  namespaces = toset([
    "apps", "cert-manager", "colegio-maria-rosario-staging", "databases",
    "diagnostics", "filebrowser", "logging", "media", "metallb-system",
    "monitoring", "nfs-provisioner", "security", "traefik"
  ])
  releases = jsondecode(file("${path.module}/../../../stacks/kubernetes/helm/releases.json"))
}
