# Credentials are supplied externally by the operator through provider-supported
# environment variables (KUBE_HOST/KUBE_TOKEN/KUBE_CLUSTER_CA_CERT_DATA).
# This code deliberately contains no kubeconfig path, token or Secret resource.
provider "kubernetes" {
  host = var.cluster_endpoint
}

provider "helm" {
  kubernetes {
    host = var.cluster_endpoint
  }
}
