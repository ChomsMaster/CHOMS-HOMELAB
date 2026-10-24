resource "kubernetes_namespace_v1" "platform" {
  for_each = local.namespaces
  metadata {
    name = each.key
  }
  lifecycle {
    prevent_destroy = true
    # Namespace labels/annotations have existing owners; adoption must not erase them.
    ignore_changes = [metadata[0].labels, metadata[0].annotations]
  }
}

resource "helm_release" "platform" {
  for_each         = local.releases
  name             = each.key
  namespace        = kubernetes_namespace_v1.platform[each.value.namespace].metadata[0].name
  repository       = each.value.repository
  chart            = each.value.chart
  version          = each.value.version
  create_namespace = false
  atomic           = true
  cleanup_on_fail  = true
  wait             = true
  wait_for_jobs    = true
  timeout          = 900
  values           = [for value_file in each.value.values : file("${path.module}/../../../${value_file}")]
  lifecycle {
    prevent_destroy = true
  }
}
