output "managed_namespaces" {
  description = "Namespace names only; no cluster credentials."
  value       = sort(keys(kubernetes_namespace_v1.platform))
}

output "helm_releases" {
  description = "Declared chart contract, not proof of adoption or runtime health."
  value = {
    for name, release in local.releases : name => {
      namespace = release.namespace
      chart     = release.chart
      version   = release.version
    }
  }
}
